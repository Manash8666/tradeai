import { motion } from 'framer-motion';
import { Fingerprint, AlertOctagon, CheckCircle2, ShieldAlert } from 'lucide-react';
import { useState, useEffect } from 'react';

export function SEBI1TouchAuth() {
  const [pendingOrders, setPendingOrders] = useState(0);
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [authorized, setAuthorized] = useState(false);

  // Simulating the Python HITL WebSocket queue
  useEffect(() => {
    const queueInterval = setInterval(() => {
        // AI randomly generates a highly profitable execution signal
        if (Math.random() > 0.8 && pendingOrders === 0) {
            setPendingOrders(1);
        }
    }, 4500);

    // If order sits for > 4 seconds un-authorized, it expires physically (slippage bounds)
    const expirationInterval = setInterval(() => {
        if (pendingOrders > 0 && !isAuthorizing) {
            setPendingOrders(0);
        }
    }, 4000);

    return () => {
        clearInterval(queueInterval);
        clearInterval(expirationInterval);
    };
  }, [pendingOrders, isAuthorizing]);

  const handle1TouchExecution = () => {
      setIsAuthorizing(true);
      setTimeout(() => {
          setAuthorized(true);
          setPendingOrders(0);
          setIsAuthorizing(false);
          
          // Reset explicitly showing the audit trail locked.
          setTimeout(() => setAuthorized(false), 2000);
      }, 400); // 400ms human-click capture latency
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`glass-panel p-4 border-l-4 overflow-hidden relative ${
        pendingOrders > 0 
        ? 'border-l-yellow-500 shadow-[0_0_30px_rgba(234,179,8,0.2)] bg-yellow-500/5' 
        : 'border-l-green-500'
      }`}
    >
      <div className="relative z-10 flex items-center justify-between">
        
        {/* Left Side: Compliance Status */}
        <div className="flex items-center gap-4">
           {pendingOrders > 0 ? (
               <div className="relative">
                 <AlertOctagon size={32} className="text-yellow-400 animate-pulse relative z-10" />
                 <div className="absolute inset-0 bg-yellow-400 rounded-full animate-ping opacity-20"></div>
               </div>
           ) : authorized ? (
               <CheckCircle2 size={32} className="text-emerald-400" />
           ) : (
               <ShieldAlert size={32} className="text-green-400" />
           )}

           <div>
              <h2 className="text-lg font-black text-white flex items-center gap-2">
                 SEBI '1-TOUCH' COMPLIANCE (APR 2026)
              </h2>
              <div className="text-xs text-gray-400 font-mono mt-0.5">
                  {pendingOrders > 0 
                   ? <span className="text-yellow-400 font-bold">1 AI SIGNAL PENDING. WAITING HUMAN AUTH.</span> 
                   : "100% Autonomous Execution Locked. Platform operates legally purely as Advisory."}
              </div>
           </div>
        </div>

        {/* Right Side: The physical Authorization Button */}
        <div>
           <button 
              onMouseDown={handle1TouchExecution}
              disabled={pendingOrders === 0 || isAuthorizing}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-black font-mono tracking-widest transition-all duration-300 ${
                  pendingOrders > 0 && !authorized
                  ? 'bg-yellow-500 text-black hover:bg-yellow-400 hover:scale-105 hover:shadow-[0_0_20px_rgba(234,179,8,0.5)] cursor-pointer'
                  : authorized
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 cursor-not-allowed'
                  : 'bg-[#0b101e] border border-gray-800 text-gray-600 cursor-not-allowed'
              }`}
           >
              <Fingerprint size={20} className={pendingOrders > 0 ? 'animate-pulse' : ''} />
              {authorized ? 'ORDER FIRED TO RUST' : isAuthorizing ? 'VERIFYING JWT...' : 'AUTHORIZE EXECUTION'}
           </button>
        </div>
      </div>
    </motion.div>
  );
}
