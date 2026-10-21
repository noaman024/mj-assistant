import asyncio
import sys
import logging

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from backend.config.settings import USER_NAME, ASSISTANT_NAME
from backend.core.orchestrator import orchestrator
from backend.voice.tts import tts
from backend.voice.stt import stt

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s")
logger = logging.getLogger("MJ.Main")

async def voice_loop():
    print("=" * 60)
    print(f"🎤 [LIVE MIC ACTIVE] Hands-Free Voice Mode Chalu Hai!")
    print(f"Boliye {USER_NAME}, MJ aapki aawaz sun rahi hai... (Exit bolne par band hoga)")
    print("=" * 60)
    
    greeting = f"Hey {USER_NAME}! Mic on hai, kahiye kya karna hai?"
    print(f"[{ASSISTANT_NAME}]: {greeting}")
    await tts.speak(greeting)

    stt.calibrate_noise(0.5)

    while True:
        try:
            print("\n🎙️ [SUN RAHI HU] Boliye...")
            spoken = await asyncio.to_thread(stt.listen_command, 10.0)

            if not spoken:
                continue

            print(f"\n🗣️ [{USER_NAME} Spoke]: '{spoken}'")

            if any(w in spoken.lower() for w in ["exit", "quit", "band karo", "bye"]):
                farewell = f"Bye {USER_NAME}!"
                print(f"[{ASSISTANT_NAME}]: {farewell}")
                await tts.speak(farewell)
                break

            response = await orchestrator.process_command(spoken)
            print(f"[{ASSISTANT_NAME}]: {response}")

        except (KeyboardInterrupt, EOFError):
            print("\nShutting down MJ.")
            break
        except Exception as e:
            logger.error(f"Voice loop error: {e}")

async def text_loop():
    print("=" * 60)
    print(f"⌨️ [TEXT MODE ACTIVE] Type kijiye {USER_NAME}!")
    print("=" * 60)
    
    greeting = f"Hey {USER_NAME}!"
    print(f"[{ASSISTANT_NAME}]: {greeting}")
    await tts.speak(greeting)

    while True:
        try:
            user_input = input(f"\n[{USER_NAME}] > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "bye"]:
                farewell = f"Bye {USER_NAME}!"
                print(f"[{ASSISTANT_NAME}]: {farewell}")
                await tts.speak(farewell)
                break

            response = await orchestrator.process_command(user_input)
            print(f"[{ASSISTANT_NAME}]: {response}")

        except (KeyboardInterrupt, EOFError):
            print("\nShutting down MJ.")
            break
        except Exception as e:
            logger.error(f"Error: {e}")

def start_bridge_server():
    try:
        import uvicorn
        from backend.bridge.server import app, print_connection_banner
        from backend.config.settings import API_PORT
        print_connection_banner(API_PORT)
        uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="warning")
    except Exception as e:
        logger.warning(f"Could not start Bridge Server: {e}")

async def main():
    import threading
    server_thread = threading.Thread(target=start_bridge_server, daemon=True)
    server_thread.start()

    # Start Autonomous Background Scheduler & Event Watchdog
    from backend.core.proactive_scheduler import proactive_scheduler
    await proactive_scheduler.start()

    args = [arg.lower() for arg in sys.argv[1:]]

    if any(a in args for a in ["--help", "-h"]):
        print("=" * 60)
        print(f"🤖 {ASSISTANT_NAME} AI Assistant - Commands & Modes")
        print("=" * 60)
        print("Usage: python main.py [option]")
        print("\nOptions:")
        print("  --gui, -g, --app, --cockpit : Open Futuristic Cockpit Window + Voice Mode")
        print("  --text, -t                 : Start Interactive Text Chat Mode")
        print("  --voice, -v                : Start Hands-Free Live Voice Mode (Default)")
        print("  --help, -h                 : Show this help message")
        return

    # Check CLI flags
    if any(a in args for a in ["--gui", "-g", "--app", "--cockpit"]):
        from backend.bridge.launcher import launch_desktop_app
        print(f"\n🚀 Launching Holographic Desktop Cockpit for {USER_NAME}...")
        launch_desktop_app()
        if any(a in args for a in ["--text", "-t"]):
            await text_loop()
        else:
            await voice_loop()
        return

    if any(a in args for a in ["--text", "-t"]):
        await text_loop()
        return

    if any(a in args for a in ["--voice", "-v"]):
        await voice_loop()
        return

    # Interactive menu if no specific CLI flag passed
    print("=" * 60)
    print(f"🤖 {ASSISTANT_NAME} Personal AI Assistant")
    print(f"👤 Master: {USER_NAME}")
    print("=" * 60)
    print("Kaise baat karna chahte hain?")
    print("  1. 🎤 Live Voice Mode (Mic se bolkar baat karein - DEFAULT)")
    print("  2. ⌨️ Text Mode (Type karke command dein)")
    print("  3. 🖥️ Desktop Cockpit Mode (Open Holographic Window + Voice)")
    print("=" * 60)
    
    try:
        choice = input("Enter choice (1 for Voice, 2 for Text, 3 for Cockpit, or press Enter for Voice) > ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "1"
    
    if choice == "3":
        from backend.bridge.launcher import launch_desktop_app
        launch_desktop_app()
        await voice_loop()
    elif choice == "2":
        await text_loop()
    else:
        await voice_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print(f"\n[{ASSISTANT_NAME}]: Alvida {USER_NAME}!")
        sys.exit(0)
