//! Kernel-Bypass UDP Packet Ingestion with DPDK Poll-Mode Driver (PMD)
//! Unbinds the hardware NIC from Linux entirely via uio_pci_generic or vfio-pci,
//! eliminating interrupts and running continuous spin-polling on a dedicated physical core.

#[repr(C)]
pub struct RteMbuf {
    pub buf_addr: *mut u8,
    pub data_off: u16,
    pub refcnt: u16,
    pub nb_segs: u16,
    pub port: u16,
    pub ol_flags: u64,
    pub packet_type: u32,
    pub pkt_len: u32,
    pub data_len: u16,
}

#[cfg(target_os = "linux")]
extern "C" {
    pub fn rte_eal_init(argc: i32, argv: *mut *mut i8) -> i32;
    pub fn rte_pktmbuf_pool_create(
        name: *const i8,
        n: u32,
        cache_size: u32,
        priv_size: u16,
        data_room_size: u16,
        socket_id: i32,
    ) -> *mut std::ffi::c_void;
    pub fn rte_eth_rx_burst(
        port_id: u16,
        queue_id: u16,
        rx_pkts: *mut *mut RteMbuf,
        nb_pkts: u16,
    ) -> u16;
    pub fn rte_pktmbuf_free(m: *mut RteMbuf);
}

pub struct DpdkReceiver {
    pub port_id: u16,
    pub queue_id: u16,
    pub burst_buffer: [*mut RteMbuf; 64],
}

impl DpdkReceiver {
    pub fn new(port_id: u16, queue_id: u16) -> Self {
        Self {
            port_id,
            queue_id,
            burst_buffer: [std::ptr::null_mut(); 64],
        }
    }

    #[cfg(target_os = "linux")]
    #[inline(always)]
    pub fn poll_burst<F>(&mut self, mut on_packet: F)
    where
        F: FnMut(&[u8]),
    {
        unsafe {
            let nb_rx = rte_eth_rx_burst(
                self.port_id,
                self.queue_id,
                self.burst_buffer.as_mut_ptr(),
                64,
            );

            for i in 0..nb_rx as usize {
                let mbuf = *self.burst_buffer.get_unchecked(i);
                let payload_ptr = (*mbuf).buf_addr.add((*mbuf).data_off as usize);
                let len = (*mbuf).data_len as usize;

                // Strip UDP/IP headers (42 bytes) directly out of Hugepage memory
                if len > 42 {
                    let packet_slice = std::slice::from_raw_parts(payload_ptr.add(42), len - 42);
                    on_packet(packet_slice);
                }

                // Return mbuf directly to DPDK lockless ring pool
                rte_pktmbuf_free(mbuf);
            }
        }
    }

    #[cfg(not(target_os = "linux"))]
    #[inline(always)]
    pub fn poll_simulated_burst<F>(&mut self, packets: &[&[u8]], mut on_packet: F)
    where
        F: FnMut(&[u8]),
    {
        for p in packets {
            if p.len() > 42 {
                on_packet(&p[42..]);
            }
        }
    }
}
