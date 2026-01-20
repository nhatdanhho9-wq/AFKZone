#!/usr/bin/env python3
"""
AFKZone Host Agent (Phase 1 - Python/aiortc)
Real screen capture + WebRTC streaming via our signaling.
"""
import asyncio
import json
import sys
import time
import numpy as np
import mss
import websockets
from av import VideoFrame
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, VideoStreamTrack

WS_URL = "ws://171.253.168.44:21121"
FPS = 15
SCALE = 0.5


class ScreenCaptureTrack(VideoStreamTrack):
    kind = "video"
    
    def __init__(self):
        super().__init__()
        self.sct = mss.mss()
        
    async def recv(self):
        pts, time_base = await self.next_timestamp()
        monitor = self.sct.monitors[1]
        sct_img = self.sct.grab(monitor)
        img = np.array(sct_img)[:, :, :3]
        
        if SCALE != 1.0:
            import cv2
            width = int(img.shape[1] * SCALE)
            height = int(img.shape[0] * SCALE)
            img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
        
        frame = VideoFrame.from_ndarray(img, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base
        await asyncio.sleep(1.0 / FPS)
        return frame


async def run_host(session_id):
    ws_url = f"{WS_URL}/sessions/{session_id}/ws?role=host"
    print(f"[HOST] Session: {session_id}")
    print(f"[HOST] Connecting to: {ws_url}")
    
    pc = RTCPeerConnection()
    print("[HOST] Adding screen capture track...")
    video_track = ScreenCaptureTrack()
    pc.addTrack(video_track)
    print("[HOST] TRACK_ADDED - OK")
    
    ice_candidates = []
    
    @pc.on("icecandidate")
    async def on_ice_candidate(candidate):
        if candidate:
            ice_candidates.append({
                "type": "ICE_CANDIDATE",
                "candidate": candidate.candidate,
                "sdpMid": candidate.sdpMid,
                "sdpMLineIndex": candidate.sdpMLineIndex
            })
    
    @pc.on("connectionstatechange")
    async def on_connection_state_change():
        print(f"[HOST] Connection state: {pc.connectionState}")
        if pc.connectionState == "connected":
            print("[HOST] WebRTC CONNECTED - Streaming!")
    
    async with websockets.connect(ws_url) as ws:
        print("[HOST] WS_CONNECT - OK")
        
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        await ws.send(json.dumps({
            "type": "SDP_OFFER",
            "sdp": pc.localDescription.sdp
        }))
        print("[HOST] SDP_OFFER sent")
        
        await asyncio.sleep(1)
        
        for ice in ice_candidates:
            await ws.send(json.dumps(ice))
            print("[HOST] ICE_CANDIDATE sent")
        
        try:
            async for msg in ws:
                data = json.loads(msg)
                msg_type = data.get("type")
                print(f"[HOST] Received: {msg_type}")
                
                if msg_type == "SDP_ANSWER":
                    answer = RTCSessionDescription(sdp=data["sdp"], type="answer")
                    await pc.setRemoteDescription(answer)
                    print("[HOST] SDP_ANSWER processed")
                    
                elif msg_type == "ICE_CANDIDATE":
                    try:
                        candidate = RTCIceCandidate(
                            sdpMid=data.get("sdpMid", "0"),
                            sdpMLineIndex=data.get("sdpMLineIndex", 0),
                            candidate=data.get("candidate", "")
                        )
                        await pc.addIceCandidate(candidate)
                        print("[HOST] ICE_CANDIDATE added")
                    except Exception as e:
                        print(f"[HOST] ICE error: {e}")
                        
                elif msg_type == "INPUT_EVENT":
                    payload = data.get("payload", {})
                    print(f"[HOST] INPUT_EVENT: {payload.get('type')}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("[HOST] WS disconnected")
        
        print("[HOST] Streaming active. Press Ctrl+C to stop.")
        while pc.connectionState == "connected":
            await asyncio.sleep(1)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python aiortc_host.py <session_id>")
        sys.exit(1)
    
    session_id = sys.argv[1]
    
    try:
        await run_host(session_id)
    except KeyboardInterrupt:
        print("[HOST] Stopped")
    except Exception as e:
        print(f"[HOST] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
