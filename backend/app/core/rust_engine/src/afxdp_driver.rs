//! AF_XDP Zero-Copy Socket Driver in Rust
//! Bypasses the Linux network stack by allowing the NIC to transfer
//! raw ethernet frames directly into user-space memory via DMA (UMEM).

// Align payload to 64-byte cache lines
#[repr(C, packed)]
#[derive(Debug, Copy, Clone)]
pub struct RawEthernetHeader {
    pub dest_mac: [u8; 6],
    pub src_mac: [u8; 6],
    pub ether_type: u16,
}

#[repr(C, packed)]
#[derive(Debug, Copy, Clone)]
pub struct RawIpv4Header {
    pub version_ihl: u8,
    pub tos: u8,
    pub total_len: u16,
    pub id: u16,
    pub frag_off: u16,
    pub ttl: u8,
    pub protocol: u8,
    pub checksum: u16,
    pub src_ip: [u8; 4],
    pub dest_ip: [u8; 4],
}

#[repr(C, packed)]
#[derive(Debug, Copy, Clone)]
pub struct RawUdpHeader {
    pub src_port: u16,
    pub dest_port: u16,
    pub len: u16,
    pub checksum: u16,
}

pub const UDP_PAYLOAD_OFFSET: usize = 42; // Ethernet [14] + IPv4 [20] + UDP [8]

#[cfg(target_os = "linux")]
use {
    std::num::NonZeroU32,
    std::sync::Arc,
    xsk_rs::{
        config::{BindFlags, QueueSize, SocketConfig, UmemConfig},
        FillQueue, FrameDesc, RxQueue, Socket, Umem,
    },
};

#[cfg(target_os = "linux")]
pub struct AfXdpDriver {
    umem: Arc<Umem>,
    fill_q: FillQueue,
    rx_q: RxQueue,
    socket: Socket,
    descs: Vec<FrameDesc>,
}

#[cfg(target_os = "linux")]
impl AfXdpDriver {
    pub fn new(if_name: &str, queue_id: u32) -> Result<Self, Box<dyn std::error::Error>> {
        // 1. Configure UMEM: 4096 chunks of 2048 bytes each
        let umem_config = UmemConfig::default();
        let frame_count = 4096;
        let (umem, fill_q, _comp_q, frame_descs) = Umem::builder()
            .config(umem_config)
            .create_and_fill(
                NonZeroU32::new(frame_count).unwrap(),
                QueueSize::new(2048).unwrap(),
                QueueSize::new(2048).unwrap(),
            )?;

        // 2. Configure zero-copy XSK socket with kernel wake-up optimization
        let socket_config = SocketConfig::builder()
            .rx_queue_size(QueueSize::new(2048).unwrap())
            .tx_queue_size(QueueSize::new(2048).unwrap())
            .bind_flags(BindFlags::XDP_ZEROCOPY | BindFlags::XDP_USE_NEED_WAKEUP)
            .build();

        let (socket, rx_q, _tx_q) = Socket::new(
            socket_config,
            &umem,
            &if_name.parse()?,
            queue_id,
        )?;

        let mut driver = Self {
            umem: Arc::new(umem),
            fill_q,
            rx_q,
            socket,
            descs: Vec::with_capacity(256),
        };

        // Populate initial frames into kernel fill ring
        unsafe {
            driver.fill_q.produce(&frame_descs)?;
        }

        Ok(driver)
    }

    /// Spin-loop hot-path: in-place zero-copy ingestion
    #[inline(always)]
    pub fn poll_next_packet<F>(&mut self, mut handle_packet: F)
    where
        F: FnMut(&[u8]),
    {
        let rcvd = match self.rx_q.poll_and_consume(&mut self.descs, 100) {
            Ok(count) if count > 0 => count,
            _ => {
                if self.rx_q.needs_wakeup() {
                    let _ = self.socket.wake_rx();
                }
                return;
            }
        };

        for desc in self.descs.iter() {
            let frame_ptr = unsafe { self.umem.data(desc) };
            let frame_slice = unsafe {
                std::slice::from_raw_parts(frame_ptr, desc.len() as usize)
            };

            if frame_slice.len() > UDP_PAYLOAD_OFFSET {
                let payload = &frame_slice[UDP_PAYLOAD_OFFSET..];
                handle_packet(payload);
            }
        }

        let recycled = unsafe { self.fill_q.produce(&self.descs) };
        if let Err(_) = recycled {
            if self.fill_q.needs_wakeup() {
                let _ = self.socket.wake_rx();
            }
        }
        self.descs.clear();
    }
}

/// Fallback / Simulation Driver for non-Linux host testing
#[cfg(not(target_os = "linux"))]
pub struct SimulatedAfXdpDriver {
    pub if_name: String,
    pub queue_id: u32,
}

#[cfg(not(target_os = "linux"))]
impl SimulatedAfXdpDriver {
    pub fn new(if_name: &str, queue_id: u32) -> Self {
        Self {
            if_name: if_name.to_string(),
            queue_id,
        }
    }

    #[inline(always)]
    pub fn poll_packet_slice<F>(&self, raw_frame: &[u8], mut handle_packet: F)
    where
        F: FnMut(&[u8]),
    {
        if raw_frame.len() > UDP_PAYLOAD_OFFSET {
            handle_packet(&raw_frame[UDP_PAYLOAD_OFFSET..]);
        }
    }
}
