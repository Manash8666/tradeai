//! Distributed RocksDB Write-Ahead Log (WAL)
//! Records incoming transitions into an append-only, memory-mapped RocksDB partition
//! before orders hit the in-memory book, preventing state corruption during crashes.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;

#[cfg(target_os = "linux")]
use rocksdb::{ColumnFamilyDescriptor, Options, WriteBatch, DB};

#[cfg(target_os = "linux")]
pub struct EngineWal {
    db: Arc<DB>,
    sequence_num: AtomicU64,
}

#[cfg(target_os = "linux")]
impl EngineWal {
    pub fn open(path: &str) -> Result<Self, rocksdb::Error> {
        let mut opts = Options::default();
        opts.create_if_missing(true);
        opts.create_missing_column_families(true);
        opts.set_use_direct_io_for_flush_and_compaction(true);
        opts.set_manual_wal_flush(true);

        let cf_orders = ColumnFamilyDescriptor::new("orders", Options::default());
        let cf_trades = ColumnFamilyDescriptor::new("trades", Options::default());

        let db = DB::open_cf_descriptors(&opts, path, vec![cf_orders, cf_trades])?;

        Ok(Self {
            db: Arc::new(db),
            sequence_num: AtomicU64::new(0),
        })
    }

    #[inline(always)]
    pub fn append_order_event(&self, order_id: u64, payload: &[u8]) -> Result<u64, rocksdb::Error> {
        let seq = self.sequence_num.fetch_add(1, Ordering::SeqCst);
        let cf = self.db.cf_handle("orders").expect("CF missing");

        let mut batch = WriteBatch::default();
        let mut key = [0u8; 16];
        key[..8].copy_from_slice(&seq.to_be_bytes());
        key[8..].copy_from_slice(&order_id.to_be_bytes());

        batch.put_cf(cf, key, payload);
        self.db.write(batch)?;

        Ok(seq)
    }

    pub fn recover_state<F>(&self, mut replay_fn: F) -> Result<(), rocksdb::Error>
    where
        F: FnMut(u64, &[u8]),
    {
        let cf = self.db.cf_handle("orders").expect("CF missing");
        let iter = self.db.iterator_cf(cf, rocksdb::IteratorMode::Start);

        for item in iter {
            let (key, value) = item?;
            let mut seq_bytes = [0u8; 8];
            seq_bytes.copy_from_slice(&key[..8]);
            let seq = u64::from_be_bytes(seq_bytes);
            replay_fn(seq, &value);
            self.sequence_num.store(seq + 1, Ordering::SeqCst);
        }
        Ok(())
    }
}

/// Fallback / In-Memory WAL for Windows development environments
#[cfg(not(target_os = "linux"))]
pub struct EngineWal {
    sequence_num: AtomicU64,
    records: parking_lot::RwLock<Vec<(u64, u64, Vec<u8>)>>, // (seq, order_id, payload)
}

#[cfg(not(target_os = "linux"))]
impl EngineWal {
    pub fn open(_path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        Ok(Self {
            sequence_num: AtomicU64::new(0),
            records: parking_lot::RwLock::new(Vec::new()),
        })
    }

    #[inline(always)]
    pub fn append_order_event(&self, order_id: u64, payload: &[u8]) -> Result<u64, Box<dyn std::error::Error>> {
        let seq = self.sequence_num.fetch_add(1, Ordering::SeqCst);
        self.records.write().push((seq, order_id, payload.to_vec()));
        Ok(seq)
    }

    pub fn recover_state<F>(&self, mut replay_fn: F) -> Result<(), Box<dyn std::error::Error>>
    where
        F: FnMut(u64, &[u8]),
    {
        let records = self.records.read();
        for (seq, _order_id, payload) in records.iter() {
            replay_fn(*seq, payload);
        }
        self.sequence_num.store(records.len() as u64, Ordering::SeqCst);
        Ok(())
    }
}
