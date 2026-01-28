import ctypes
from ctypes import wintypes

def get_session_id(process_id=None):
    ProcessIdToSessionId = ctypes.windll.kernel32.ProcessIdToSessionId
    ProcessIdToSessionId.argtypes = [wintypes.DWORD, wintypes.PDWORD]
    ProcessIdToSessionId.restype = wintypes.BOOL
    session_id = wintypes.DWORD()
    if process_id is None:
        process_id = wintypes.DWORD(ctypes.windll.kernel32.GetCurrentProcessId())
    else:
        wintypes.DWORD(process_id)
    if ProcessIdToSessionId(process_id, ctypes.byref(session_id)):
        return session_id.value 
    else:
        return None
