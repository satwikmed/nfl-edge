"use client";

import { useEffect, useState } from "react";
import { Warp } from "@paper-design/shaders-react";

export default function BackgroundShader() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 w-full h-full z-0 pointer-events-none overflow-hidden select-none">
      <div className="absolute inset-0">
        <Warp
          style={{ height: "100%", width: "100%" }}
          proportion={0.45}
          softness={1}
          distortion={0.25}
          swirl={0.8}
          swirlIterations={10}
          shape="checks"
          shapeScale={0.1}
          scale={1}
          rotation={0}
          speed={0.4} // elegant, slow movement suited for background
          colors={["hsl(200, 100%, 15%)", "hsl(160, 100%, 58%)", "hsl(180, 90%, 22%)", "hsl(170, 100%, 60%)"]}
        />
      </div>
      {/* Precision 35% dark overlay to achieve perfect legibility while preserving vibrant shader depth */}
      <div className="absolute inset-0 bg-black/35 backdrop-blur-[1px]" />
    </div>
  );
}
