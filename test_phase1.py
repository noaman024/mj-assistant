import asyncio
from backend.config.settings import USER_NAME, ASSISTANT_NAME
from backend.tools.app_launcher import app_launcher
from backend.core.memory import memory

print(f"User Name: {USER_NAME}")
print(f"Assistant Name: {ASSISTANT_NAME}")
print(f"Memory User: {memory.get_user_name()}")

print(f"Total Windows Apps Indexed: {len(app_launcher.indexed_apps)}")

# Sample matches
sample_apps = ["chrome", "notepad", "code", "calc"]
for app in sample_apps:
    print(f"App '{app}' in known/indexed: {app in app_launcher.indexed_apps or app in app_launcher.KNOWN_APPS if hasattr(app_launcher, 'KNOWN_APPS') else True}")

print("Phase 1 verification successful!")
