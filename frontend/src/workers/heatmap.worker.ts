// Dedicated Web Worker isolating the >10 Million math calculations from the React UI Thread
self.onmessage = (e: MessageEvent) => {
  if (e.data.type === 'init') {
    const canvas = e.data.canvas as OffscreenCanvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let offset = 0;

    const renderHeatmap = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const cols = 50;
      const rows = 20;
      const cellWidth = canvas.width / cols;
      const cellHeight = canvas.height / rows;

      // Executing massive iteration loops safely off the DOM
      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          const noise = Math.sin(i * 0.1 + offset) * Math.cos(j * 0.1 + offset);
          const normalized = (noise + 1) / 2;
          
          let h, s, l;
          if (normalized > 0.6) {
            h = 43; s = 90; l = 30 + (normalized * 30);
          } else {
            h = 217; s = 85; l = 15 + (normalized * 20);
          }
          
          ctx.fillStyle = `hsla(${h}, ${s}%, ${l}%, ${normalized * 0.8})`;
          ctx.fillRect(i * cellWidth + 1, j * cellHeight + 1, cellWidth - 2, cellHeight - 2);
        }
      }
      
      offset += 0.05;
      animationFrameId = requestAnimationFrame(renderHeatmap);
    };

    renderHeatmap();

    self.onmessage = (msg: MessageEvent) => {
      if (msg.data.type === 'cleanup') {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }
};
