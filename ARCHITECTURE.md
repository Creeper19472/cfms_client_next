# Download Manager Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CFMS Client Application                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐            ┌──────────────┐
│  Files View  │          │  Tasks View  │            │  Home View   │
│              │          │              │            │              │
│  [Explorer]  │          │  [Monitor]   │            │  [Welcome]   │
└──────────────┘          └──────────────┘            └──────────────┘
        │                           │                           
        │ User clicks file          │ Display tasks            
        │ to download               │ & progress               
        ▼                           │                          
┌──────────────────────────────────┐│                          
│   get_document()                 ││                          
│   - Request from server          ││                          
│   - Submit to download manager   ││                          
└──────────────────────────────────┘│                          
        │                           │                          
        │ Add Task                  │ Register Callback        
        ▼                           ▼                          
┌─────────────────────────────────────────────────────────────┐
│              DownloadManagerService                         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Task Queue                                           │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │ │
│  │  │ PENDING  │→ │ PENDING  │→ │ PENDING  │           │ │
│  │  └──────────┘  └──────────┘  └──────────┘           │ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                  │
│         ┌────────────────┼────────────────┐                │
│         │                │                │                │
│         ▼                ▼                ▼                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│  │ Download │    │ Download │    │ Download │            │
│  │  Task 1  │    │  Task 2  │    │  Task 3  │            │
│  │  [ACTIVE]│    │  [ACTIVE]│    │  [ACTIVE]│            │
│  └──────────┘    └──────────┘    └──────────┘            │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │ Max 3 concurrent                │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Active Tasks                                       │  │
│  │  - Track running downloads                          │  │
│  │  - Monitor progress                                 │  │
│  │  - Handle cancellation                              │  │
│  │  - Notify callbacks                                 │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Progress Updates
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Callbacks (UI Updates)                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  TasksView │  │  Progress  │  │   Logs     │           │
│  │  Updates   │  │  Overlay   │  │  (Logger)  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘


Download Task State Machine:
════════════════════════════

                    ┌─────────┐
                    │ PENDING │
                    └────┬────┘
                         │
                    Queue picks up
                         │
                         ▼
                 ┌───────────────┐
                 │  DOWNLOADING  │
                 └───────┬───────┘
                         │
                    File received
                         │
                         ▼
                 ┌───────────────┐
                 │  DECRYPTING   │
                 └───────┬───────┘
                         │
                   Chunks decrypted
                         │
                         ▼
                 ┌───────────────┐
                 │   VERIFYING   │◄───── Cleaning temp files
                 └───────┬───────┘
                         │
                    ┌────┴────┐
                    │         │
            Hash valid?    Hash/size
                    │         │ mismatch
                    ▼         ▼
              ┌──────────┐ ┌────────┐
              │COMPLETED │ │ FAILED │
              └──────────┘ └────────┘
                    
              User cancel ──────────▼
                             ┌───────────┐
                             │ CANCELLED │
                             └───────────┘


Component Interaction Flow:
═══════════════════════════

1. User Action
   ├─► Click file in Files View
   └─► get_document() called

2. Task Creation
   ├─► Request document from server
   ├─► Get task_id from server
   └─► Add task to DownloadManagerService

3. Service Processing
   ├─► Check concurrent limit (max 3)
   ├─► Create async download task
   ├─► Establish WebSocket connection
   └─► Start file transfer

4. Progress Updates
   ├─► Stage 0: Downloading (bytes/total)
   ├─► Stage 1: Decrypting (chunks/total)
   ├─► Stage 2: Cleaning temp files
   └─► Stage 3: Verifying hash/size

5. UI Updates
   ├─► Callback notifies TasksView
   ├─► TaskTile updates progress bar
   ├─► Status text updated
   └─► Percentage displayed

6. Completion
   ├─► Task marked COMPLETED/FAILED
   ├─► Final callback sent
   ├─► Connection closed
   └─► Task removed from active set


Service Lifecycle:
═════════════════

main.py startup
    │
    ├─► Create ServiceManager
    │
    ├─► Create DownloadManagerService
    │   ├─► enabled=True
    │   ├─► max_concurrent=3
    │   └─► interval=1.0 (check queue every second)
    │
    ├─► Register service
    │
    ├─► Start all services
    │   └─► DownloadManagerService.start()
    │       ├─► Status: STARTING
    │       ├─► Call on_start()
    │       ├─► Create background task
    │       └─► Status: RUNNING
    │
    └─► Execute loop (every 1 second)
        ├─► Check for PENDING tasks
        ├─► Count active downloads
        ├─► Start new tasks if slots available
        └─► Continue until stop requested

page.on_close
    │
    └─► ServiceManager.stop_all()
        └─► DownloadManagerService.stop()
            ├─► Status: STOPPING
            ├─► Cancel all active downloads
            ├─► Wait for tasks to complete
            ├─► Call on_stop()
            └─► Status: STOPPED
```
