"use client";
import React, { useState } from "react";
import { GhostPanel } from "./TerminalPanel";
import Image from "next/image";

import type { Screenshot } from "@/lib/types";

export function ScoutImagery({
	screenshots
}: {
	screenshots: Screenshot[];
}) {
	const [imgIndex, setImgIndex] = useState(0);

	if (!screenshots || screenshots.length === 0) {
		return <GhostPanel message="OPTICAL_SENSOR_OFFLINE" />;
	}

	const currentImg = screenshots[imgIndex];
	// Validate image data exists
	const imageSrc = currentImg?.data || currentImg?.url;
	if (!imageSrc) {
		return <GhostPanel message="IMAGE_DATA_UNAVAILABLE" />;
	}

	// Determine if it's base64 or URL
	const srcPrefix = currentImg.data ? "data:image/jpeg;base64," : "";

	return (
		<div className="relative w-full h-[300px] border border-[var(--t-border)] overflow-hidden flex flex-col items-center justify-center p-2 bg-[#050505]">
			{/* Target Crosshairs styling */}
			<div className="absolute top-2 left-2 w-4 h-4 border-t border-l border-[var(--t-green)] opacity-50 z-10"></div>
			<div className="absolute top-2 right-2 w-4 h-4 border-t border-r border-[var(--t-green)] opacity-50 z-10"></div>
			<div className="absolute bottom-2 left-2 w-4 h-4 border-b border-l border-[var(--t-green)] opacity-50 z-10"></div>
			<div className="absolute bottom-2 right-2 w-4 h-4 border-b border-r border-[var(--t-green)] opacity-50 z-10"></div>

			<div className="px-2 w-full flex justify-between uppercase text-[10px] text-[var(--t-green)] mb-2 z-10 opacity-70">
				<span>FRAME: {imgIndex + 1}/{screenshots.length}</span>
				<span className="animate-pulse">REC</span>
			</div>

			<div className="relative w-full h-full flex items-center justify-center group overflow-hidden bg-black/50">
				<div className="relative w-[90%] h-[90%]">
					<Image
						src={`${srcPrefix}${imageSrc}`}
						alt={`Recon Frame ${imgIndex}`}
						fill
						className="object-contain opacity-80"
						unoptimized={!!currentImg.data} // Allow base64 without optimization
					/>
				</div>

				{/* Overlay hover controls */}
				<div className="absolute inset-0 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
					<button
						className="h-full px-4 bg-black/50 text-[var(--t-green)] hover:bg-[var(--t-green)] hover:text-black cursor-pointer uppercase font-bold"
						onClick={() => setImgIndex((i) => Math.max(0, i - 1))}
						disabled={imgIndex === 0}
					>
						&lt;
					</button>
					<button
						className="h-full px-4 bg-black/50 text-[var(--t-green)] hover:bg-[var(--t-green)] hover:text-black cursor-pointer uppercase font-bold"
						onClick={() => setImgIndex((i) => Math.min(screenshots.length - 1, i + 1))}
						disabled={imgIndex === screenshots.length - 1}
					>
						&gt;
					</button>
				</div>
			</div>
		</div>
	);
}