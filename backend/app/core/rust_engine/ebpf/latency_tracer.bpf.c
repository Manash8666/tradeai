// Real-Time Linux eBPF Tracing for Sub-Microsecond Profiling
// Attaches to kernel ingress (netif_receive_skb) and userspace gateway (send_order)
// to record exact hardware-to-dispatch latency in nanoseconds.

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct event_t {
    u64 ingress_ns;
    u64 dispatch_ns;
    u64 delta_ns;
    u32 pid;
    char comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10240);
    __type(key, u32);   // Packet flow hash / Seq ID
    __type(value, u64); // Timestamp (ns)
} packet_ingress_times SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24); // 16MB ring buffer
} latency_events SEC(".maps");

// 1. Kernel Network Ingress Hook
SEC("tracepoint/net/netif_receive_skb")
int trace_netif_rx(struct trace_event_raw_net_dev_template *ctx) {
    u64 ts = bpf_ktime_get_ns();
    u32 key = ctx->skbaddr & 0xFFFFFFFF;
    bpf_map_update_elem(&packet_ingress_times, &key, &ts, BPF_ANY);
    return 0;
}

// 2. Userspace Function Exit Hook (Order Gateway Dispatch)
SEC("uprobe//app/matching_engine:send_order")
int BPF_KPROBE(trace_order_dispatch, u32 skb_key) {
    u64 dispatch_ts = bpf_ktime_get_ns();
    u64 *ingress_ts = bpf_map_lookup_elem(&packet_ingress_times, &skb_key);

    if (ingress_ts) {
        struct event_t *e = bpf_ringbuf_reserve(&latency_events, sizeof(*e), 0);
        if (!e) return 0;

        e->ingress_ns = *ingress_ts;
        e->dispatch_ns = dispatch_ts;
        e->delta_ns = dispatch_ts - *ingress_ts;
        e->pid = bpf_get_current_pid_tgid() >> 32;
        bpf_get_current_comm(&e->comm, sizeof(e->comm));

        bpf_ringbuf_submit(e, 0);
        bpf_map_delete_elem(&packet_ingress_times, &skb_key);
    }
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
