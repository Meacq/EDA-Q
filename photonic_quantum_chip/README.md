# 🔬 Photonic Quantum Chip Routing System

<div align="center">

![Version](https://img.shields.io/badge/version-0.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-red.svg)

A professional automated routing system for photonic quantum chips, using advanced A* algorithm and optimized data structures, providing an intuitive visualization interface.

[Features](#-core-features) • [Installation](#-quick-start) • [Usage](#-usage-guide) • [Documentation](#-feature-details)

</div>

---

## 📖 Table of Contents

- [Project Introduction](#-project-introduction)
- [Core Features](#-core-features)
- [System Architecture](#-system-architecture)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Directory Structure](#-directory-structure)
- [Data Formats](#-data-formats)
- [Feature Details](#-feature-details)
- [FAQ](#-frequently-asked-questions)
- [Changelog](#-update-log)

---

## 🎯 Project Introduction

The Photonic Quantum Chip Routing System is an automated routing tool specifically designed for photonic quantum chips, capable of efficiently handling complex routing tasks. The system adopts a three-stage routing strategy, supports both automatic and manual modes, and provides intelligent boundary matching, path optimization, and snapshot management functions.

### Application Scenarios

- 🔹 GDS layout file processing
- 🔹 Photonic quantum chip automated routing design
- 🔹 Routing scheme visualization analysis
- 🔹 Teaching and research tool
---

## ✨ Core Features

### 🚀 Performance Optimization

- **DiagonalBitmap** - O(1) time complexity diagonal collision detection
- **Numba JIT** - Optional Just-In-Time compilation acceleration (10-50x speedup for geometric calculations)
- **8-direction A*** - Optimized A* search algorithm with diagonal movement support, generating shorter routing paths
- **Diagonal Occupancy Strategy** - Intelligent spacing control that meets routing requirements without additional spacing detection
- **Path Optimization Algorithm** - Automatically simplifies paths, removes redundant points, and optimizes routing quality

### 🎨 User Interface

- **Light Blue-White Professional Theme** - Clean and beautiful color scheme providing a comfortable visual experience
- **Scrollable Control Panel** - Adaptive layout supporting various screen sizes
- **Real-time Visualization** - High-quality graphics display based on Matplotlib, supporting zoom and pan
- **Intelligent Log System** - Hierarchical logs (INFO/WARNING/ERROR/SUCCESS) with color labeling and real-time output
- **Interactive Canvas** - Supports multiple interaction methods including polygon selection, click selection, and box selection

### 🔧 Functional Features

- ✅ **Three-Stage Routing Process** - Out internal → Center internal → External connection, clear logic
- ✅ **Intelligent Boundary Matching** - Automatically identifies parallel/L-shaped boundaries, provides 4 mapping strategies with system auto-selection of optimal strategy
- ✅ **Snapshot Management System** - Supports saving, viewing, and switching snapshots, repeatable switching, and non-linear workflow support
- ✅ **Manual/Auto Modes** - Flexible operation methods adapting to different needs and complexities
- ✅ **Data Persistence** - Supports saving/loading .pkl format routing data
- ✅ **GDS File Support** - Supports extracting coordinates from GDS files and exporting routing results to GDS
- ✅ **Unified Path Management** - Automatically creates directories and centrally manages input/output paths
- ⚠️ **Path Optimization** - Segment merging, dogleg removal, Manhattan shortcut optimization (limited functionality in current version, to be improved)
---

## 🏗️ System Architecture

### System Layered Architecture

```
┌─────────────────────────────────────────────────┐
│              User Interface Layer (UI Layer)    │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ Main Window │ │ Canvas Area │ │ Control Panel │ │
│  │MainWindow│  │ Canvas   │  │ControlPanel   │ │
│  └──────────┘  └──────────┘  └───────────────┘ │
│  ┌──────────┐  ┌──────────┐                    │
│  │ Dialogs  │  │ Log Panel │                    │
│  │ Dialogs  │  │LogPanel  │                    │
│  └──────────┘  └──────────┘                    │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│           Business Logic Layer                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ Stage 1  │  │ Stage 2  │  │   Stage 3     │ │
│  │ Stage1   │  │ Stage2   │  │   Stage3      │ │
│  │Controller│  │Controller│  │  Controller   │ │
│  └──────────┘  └──────────┘  └───────────────┘ │
│  ┌──────────┐  ┌──────────┐                    │
│  │Boundary Tool│ │Path Optimization│          │
│  │Boundary  │  │PathSmooth│                    │
│  └──────────┘  └──────────┘                    │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│           Core Algorithm Layer (Core Layer)     │
│  ┌──────────────┐  ┌───────────────────────┐   │
│  │ Advanced Router │ │ Diagonal Bitmap      │   │
│  │AdvancedRouter│  │  DiagonalBitmap       │   │
│  │ (A* Search)  │  │  (Collision Detection)│   │
│  └──────────────┘  └───────────────────────┘   │
│  ┌──────────────┐  ┌───────────────────────┐   │
│  │ Grid Manager  │ │ Geometry Tools        │   │
│  │ GridManager  │  │  Geometry Utils       │   │
│  └──────────────┘  └───────────────────────┘   │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│          Data and Storage Layer (Data Layer)    │
│  ┌──────────────┐  ┌───────────────────────┐   │
│  │ Persistence Manager │ │ Snapshot Manager  │   │
│  │PersistenceM  │  │  SnapshotManager      │   │
│  │   (.pkl)     │  │  StateManager         │   │
│  └──────────────┘  └───────────────────────┘   │
│  ┌──────────────┐                              │
│  │ GDS Tools    │                              │
│  │ GDS Tools    │                              │
│  └──────────────┘                              │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Environment Requirements

**Python Version**:
- Python 3.10 - 3.12
- Recommended: 3.12.3 (best tested version)

**Operating System**:
- Windows 10/11

**Hardware Requirements**:
- **Memory**: Minimum 4GB, recommended 8GB or more
- **Storage**: At least 500MB available space (for program and data files)

**Required Software**:
- tkinter (Python GUI library, usually installed with Python)

### Installation Steps

#### 1. Clone the Project

```bash
git clone https://github.com/your-username/photonic-chip-routing.git
cd photonic-chip-routing
```

#### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

**Basic Installation (Core Dependencies Only)**:

```bash
pip install -r requirements.txt
```

This will install the following **required core dependencies**:
- **numpy** >= 1.20.0, < 2.0.0 (recommended 1.23.x)
- **pandas** >= 1.3.0, < 3.0.0 (recommended 2.0.x)
- **matplotlib** >= 3.5.0, < 4.0.0 (recommended 3.7.x)

**Using Domestic Mirror for Faster Installation**:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

**Optional Dependencies (Install as Needed)**:

**1. Performance Optimization Package (Highly Recommended)**:

```bash
# Install Numba to enable JIT acceleration (10-50x speedup for geometric calculations)
pip install "numba>=0.55.0,<1.0.0"
# Recommended version: numba 0.57.x
```

> **Note**: If Numba is not installed, the system will automatically use pure Python implementation, which functions normally but runs slower.

**2. GDS File Processing Package (Optional)**:

```bash
# Install gdspy to support GDS file processing
pip install "gdspy>=1.6.0,<2.0.0"
# Recommended version: gdspy 1.6.x
```

> **Note**: Only install if you need to use GDS coordinate extraction and path export functionality.

**One-time Installation of All Dependencies (Including Optional)**:

```bash
pip install -r requirements.txt && pip install "numba>=0.55.0,<1.0.0" "gdspy>=1.6.0,<2.0.0"
```

#### 4. Prepare Data

Place your chip layout CSV files in the `photonic_routing/data/input/csv/` directory.

#### 5. Launch the Program

```bash
# Method 1: Run directly
python run.py

# Method 2: Run as module
python -m photonic_routing
```

---

## 📚 Usage Guide

### Basic Workflow

```
1. Import CSV Data (Ctrl+O)
   ↓
2. Start New Region (Ctrl+N)
   ↓
3. Draw Polygon to Select Routing Area
   - Left click to add vertices
   - Press Enter to confirm selection
   ↓
4. Stage 1: Out Points Internal Routing
   - Select automatic or manual mode
   - System connects Out points to boundary standby points
   ↓
5. Stage 2: Center Points Internal Routing
   - Select automatic or manual mode
   - System connects Center points to boundary standby points
   ↓
6. Stage 3: External Connection
   - System automatically identifies boundary type (parallel/L-shaped)
   - Select mapping strategy (5 options including system auto-selection)
   - Connect Center standby points to Out standby points
   ↓
7. Save Results / Continue to Next Region
```

### Detailed Operation Instructions

#### 📥 Step 1: Import Data

**Method 1: Import CSV File**
1. Click menu **File → Import CSV Data** (or press `Ctrl+O`)
2. Select your CSV file
3. System automatically parses and displays data overview
4. Log panel shows imported point statistics

**Method 2: Load Saved Routing Data**
1. Click menu **File → Load Routing Data** (or press `Ctrl+L`)
2. Select previously saved .pkl file
3. System restores previous working state, including all completed paths

#### 🎯 Step 2: Region Selection

1. Click **"Start New Region"** button (or press `Ctrl+N`)
2. Draw polygon on canvas:
   - **Left click**: Add polygon vertices
   - **Move mouse**: Preview current edge
   - **Press Enter**: Confirm selection, complete polygon
   - **Press Esc**: Cancel selection
3. System automatically filters points within the polygon
4. Log shows selected Out and Center point counts

#### 🔄 Step 3: Stage 1 - Out Points Internal Routing

**Goal**：Connect Out points to boundary standby points

**Automatic Mode** (Recommended for regular layouts)：
1. Click **"Automatic Mode"** button
2. System automatically assigns Out points to corresponding boundaries based on direction attribute
3. Automatically generates standby points (via vertical projection)
4. Automatically completes internal routing for all Out points
5. View routing results

**Manual Mode** (For complex or special layouts)：
1. Click **"Manual Mode"** button
2. System prompts to select points for each boundary direction in sequence：
   - **Top Boundary (Top)**
   - **Bottom Boundary (Bottom)**
   - **Left Boundary (Left)**
   - **Right Boundary (Right)**
3. Point selection methods：
   - **Left click**: Select single point
   - **Right drag**: Box select multiple points
   - **Ctrl+Z**: Undo last selection
   - **Press Enter**: Confirm current boundary selection
4. System automatically routes after each boundary selection

#### 🔄 Step 4: Stage 2 - Center Points Internal Routing

**Goal**：Connect Center points to boundary standby points

Operation is similar to Stage 1, but for Center points：

**Automatic Mode**：
1. Click **"Automatic Mode"** button
2. System intelligently assigns Center points to boundaries
3. Automatically generates standby points (avoiding obstacles and existing paths)
4. Completes routing in optimized order

**Manual Mode**：
1. Click **"Manual Mode"** button
2. Select Center points for top/bottom/left/right boundaries in sequence
3. Use same selection methods (click/box select)
4. Automatic routing after confirmation

**After Completion**：
- System will ask if you want to print standby point numbers
- If points < 100, numbers will be displayed on canvas
- Number information is used for Stage 3 manual mode

#### 🔄 Step 5: Stage 3 - External Connection

**Goal**：Connect Center standby points to Out standby points, complete overall routing

**Automatic Mode** (Recommended)：
1. Click **"Automatic Mode"** button
2. System automatically detects boundary type：
   - **Parallel Boundary**: Center and Out on opposite sides
   - **L-shaped Boundary**: Center and Out on adjacent sides
3. Strategy selection dialog pops up, showing 5 mapping strategies (including system auto-selection of optimal strategy)
4. Select a strategy
5. Click confirm, system automatically completes external connection

**Manual Mode** (For precise control)：
1. Click **"Manual Mode"** button
2. Enter Center standby point numbers (space-separated)
   - Example: `0 1 2 3 4`
3. Enter corresponding Out standby point numbers (space-separated)
   - Example: `5 6 7 8 9`
4. Click **"Add and Route"** button
5. System connects corresponding point pairs in order
6. Can add different point pair combinations multiple times

#### 💾 Step 6: Save Results

**Save Routing Data**：
1. Click **File → Save Routing Data** (or press `Ctrl+S`)
2. Select save location and filename
3. System saves as .pkl format, including：
   - All completed paths
   - Router state
   - Snapshot history

**Export Image**：
1. Click **File → Export Image** (or press `Ctrl+E`)
2. Select save location
3. System exports current canvas as high-resolution PNG image

**Continue to Next Region**：
- After completing current region, can directly click **"Start New Region"** to continue
- System automatically creates snapshot to save current progress
- New region routing will be based on existing paths

### Keyboard Shortcuts Reference

| Shortcut | Function | Description |
|--------|------|------|
| `Ctrl+O` | Import CSV data | Open file selection dialog |
| `Ctrl+L` | Load routing data | Load saved .pkl file |
| `Ctrl+S` | Save routing data | Save current working state |
| `Ctrl+E` | Export image | Export current canvas as PNG |
| `Ctrl+N` | Start new region | Start new routing region |
| `Ctrl+H` | View snapshot list | Show all saved snapshots |
| `Ctrl+T` | Switch to snapshot | Restore to specified snapshot |
| `F5` | Refresh canvas | Redraw canvas |
| `F1` | Usage instructions | Show help information |
| `Ctrl+Q` | Exit program | Close application |
| `Enter` | Confirm selection | Confirm current operation |
| `Esc` | Cancel operation | Cancel current operation |
| `Ctrl+Z` | Undo | Undo last selection |

---

## 📁 Directory Structure

```
photonic-chip-routing/
│
├── 📄 run.py                           # Main startup script
├── 📄 README.md                        # Project documentation
├── 📄 requirements.txt                 # Dependency list
│
└── 📂 photonic_routing/                # Main program package
    │
    ├── 📄 __init__.py                  # Package initialization
    ├── 📄 __main__.py                  # Module entry point
    ├── 📄 main.py                      # Main function
    │
    ├── 📂 config/                      # ⚙️ Configuration module
    │   ├── __init__.py
    │   ├── constants.py                # System constants (grid size, Numba config)
    │   ├── paths.py                    # Unified path management ⭐
    │   └── ui_config.py                # UI configuration (colors, fonts, canvas size)
    │
    ├── 📂 core/                        # 🎯 Core algorithms
    │   ├── __init__.py
    │   ├── data_structures.py          # DiagonalBitmap data structure
    │   ├── grid_manager.py             # Grid manager
    │   └── router.py                   # Advanced A* router
    │
    ├── 📂 managers/                    # 🗂️ State management
    │   ├── __init__.py
    │   ├── state_manager.py            # Application state management
    │   ├── snapshot_manager.py         # Snapshot management (save/restore)
    │   └── persistence_manager.py      # Data persistence (.pkl)
    │
    ├── 📂 routing/                     # 🔀 Routing controllers
    │   ├── __init__.py
    │   ├── boundary_utils.py           # Boundary matching tools
    │   ├── path_smoother.py            # Path optimization algorithm ⭐
    │   ├── path_merger.py              # Path merging logic ⭐
    │   ├── stage1.py                   # Stage 1 controller
    │   ├── stage2.py                   # Stage 2 controller
    │   └── stage3.py                   # Stage 3 controller
    │
    ├── 📂 ui/                          # 🎨 User interface
    │   ├── __init__.py
    │   ├── main_window.py              # Main window (menu, layout)
    │   ├── canvas_area.py              # Matplotlib canvas
    │   ├── control_panel.py            # Scrollable control panel
    │   ├── dialogs.py                  # Strategy selection dialogs
    │   ├── log_panel.py                # Real-time log panel
    │   └── styles.py                   # UI style definitions
    │
    ├── 📂 utils/                       # 🛠️ Utility functions
    │   ├── __init__.py
    │   ├── geometry.py                 # Geometric calculations (Numba accelerated)
    │   ├── helpers.py                  # Helper functions
    │   ├── logger.py                   # Log system
    │   └── gds_tools.py                # GDS file processing tools ⭐
    │
    └── 📂 data/                        # 💾 Data directory
        ├── 📂 input/                   # Input data
        │   ├── csv/                    # CSV files
        │   └── gds/                    # GDS files
        └── 📂 output/                  # Output results
            ├── routing/                # Routing data (.pkl)
            ├── figures/                # Images (.png)
            └── gds/                    # GDS output
```

**Directory Description**:

- **config/**: System configuration, including constant definitions, path management, UI configuration
- **core/**: Core algorithm implementation, including A* router, grid management, data structures
- **managers/**: State and data management, including snapshots, persistence, application state
- **routing/**: Three-stage routing controllers and auxiliary tools
- **ui/**: User interface components, including main window, canvas, control panel, dialogs
- **utils/**: General utility functions, including geometric calculations, logging, GDS processing
- **data/**: Data storage directory, automatically created, containing input and output subdirectories

---

## 📋 Data Formats

### CSV Input Format

The system supports standard CSV format for chip layout data.

**Required Fields**:

```csv
x,y,layer,direction
100.5,200.3,out,top
150.2,250.8,center,
200.0,300.0,obstacle,
180.5,280.3,chip_range,
```

**Field Description**:

| Field | Type | Required | Description |
|------|------|------|------|
| `x` | Float | ✅ | X coordinate |
| `y` | Float | ✅ | Y coordinate |
| `layer` | String | ✅ | Point type |
| `direction` | String | ⚠️ | Direction for Out points (only required for Out points) |

**layer Types**:

- `out` - Output connection points (need to connect to chip boundary)
- `center` - Center connection points (need to connect to Out points)
- `obstacle` - Obstacles (need to be avoided during routing)
- `chip_range` - Chip range markers (define chip boundaries)

**direction Values** (only for `out` type):

- `top` - Top boundary
- `bottom` - Bottom boundary
- `left` - Left boundary
- `right` - Right boundary

**Example CSV File**:

```csv
x,y,layer,direction
100,200,out,top
150,200,out,top
200,200,out,right
100,150,center,
150,150,center,
200,150,center,
50,50,obstacle,
250,250,obstacle,
0,0,chip_range,
300,300,chip_range,
```

### PKL Output Format

The system uses Python pickle format to save routing data, including the complete working state.

**Data Structure**:

```python
{
    'task_count': int,              # Region number (starting from 1)
    'timestamp': str,               # Save timestamp
    'router_state': {               # Router state
        'occupation_grid': ndarray, # Occupation grid (numpy array)
        'diagonal_bitmap': DiagonalBitmap,  # Diagonal bitmap
        'global_reserved_points': set,      # Global reserved points set
        'h': int,                   # Grid height
        'w': int                    # Grid width
    },
    'all_finished_paths': [         # All completed paths
        {
            'path': [(x1,y1), (x2,y2), ...],  # Path coordinate list
            'net_id': int,          # Network ID
            'stage': str,           # Belonging stage
            'region': int           # Belonging region
        },
        ...
    ],
    'snapshots': [                  # Snapshot list (optional)
        {
            'region_num': int,      # Snapshot region number
            'timestamp': str,       # Snapshot time
            'router_state': {...},  # Router state at snapshot
            'paths': [...]          # Paths at snapshot
        },
        ...
    ]
}
```

**Loading PKL File**:

```python
import pickle

with open('routing_data.pkl', 'rb') as f:
    data = pickle.load(f)

print(f"Region count: {data['task_count']}")
print(f"Path count: {len(data['all_finished_paths'])}")
print(f"Snapshot count: {len(data.get('snapshots', []))}")
```

### GDS File Support

The system provides GDS file processing tools with UI interface, supporting coordinate extraction from GDS and exporting routing results, with the following specific logic:

**Extracting Coordinates from GDS**:

```python
from photonic_routing.utils.gds_tools import extract_coordinates_from_gds

# Extract rectangle coordinates for specified cell and layer
coords = extract_coordinates_from_gds(
    gds_file='input.gds',
    cell_name='TOP',
    layer=1,
    size_filter=(10, 10)  # Optional: filter specific sizes
)
```

**Exporting to GDS**:

```python
from photonic_routing.utils.gds_tools import export_paths_to_gds

# Export routing paths to GDS
export_paths_to_gds(
    paths=all_finished_paths,
    output_file='output.gds',
    layer=2,
    datatype=0
)
```

---

## 🔍 Feature Details

### Three-Stage Routing Strategy

The system adopts a phased routing strategy, breaking down complex routing tasks into three clear stages.

#### Stage 1: Out Points (Outer Points/End Points) Internal Routing

**Goal**: Connect Out points to chip boundary

**Working Principle**:
1. Map Out points to corresponding boundaries based on their direction attribute
2. Generate standby points on boundaries (via vertical projection)
3. Use A* algorithm to route from Out points to standby points
4. Standby points serve as starting points for subsequent external connections

**Advantages**:
- Simplifies internal routing, avoiding complex crossings
- Provides regular interfaces for external connections
- Supports both automatic and manual modes

#### Stage 2: Center Points (Inner Points/Start Points) Internal Routing

**Goal**: Connect Center points to chip boundary

**Working Principle**:
1. Intelligently allocate Center points to boundaries (based on distance and load balancing)
2. Generate standby points on boundaries (avoiding obstacles and existing paths)
3. Route in optimized order (reducing conflicts)
4. Standby points serve as end points for external connections

**Advantages**:
- Automatic load balancing, avoiding overcrowding on any single boundary
- Intelligent obstacle avoidance, improving routing success rate
- Optimized routing order, reducing rework

#### Stage 3: External Connection

**Goal**: Connect Center standby points to Out standby points

**Working Principle**:
1. Automatically detect boundary type (parallel/L-shaped)
2. Provide 4 mapping strategies for selection
3. Connect corresponding standby point pairs in strategic order
4. Complete overall routing

**Boundary Types**:

**Parallel Boundary**: Center and Out on opposite sides
- Example: Center on top boundary, Out on bottom boundary
- Example: Center on left boundary, Out on right boundary

**L-shaped Boundary**: Center and Out on adjacent sides
- Example: Center on top boundary, Out on right boundary
- Example: Center on left boundary, Out on bottom boundary

**Mapping Strategies**:

For **Parallel Boundary** (horizontal example):
1. **Strategy 1**：Leftmost Center ↔ Leftmost Out, pair sequentially to the right
2. **Strategy 2**：Leftmost Center ↔ Rightmost Out, pair sequentially in opposite direction
3. **Strategy 3**：Rightmost Center ↔ Leftmost Out, pair sequentially in opposite direction
4. **Strategy 4**：Rightmost Center ↔ Rightmost Out, pair sequentially to the left

For **L-shaped Boundary**:
1. **Strategy 1**：Vertical top to bottom + Horizontal left to right
2. **Strategy 2**：Vertical top to bottom + Horizontal right to left
3. **Strategy 3**：Vertical bottom to top + Horizontal left to right
4. **Strategy 4**：Vertical bottom to top + Horizontal right to left

### Path Optimization Features (Under Development)

The system provides path optimization algorithm interfaces to improve routing quality.

**⚠️ Important Note**:
- **Current Status**: Path optimization algorithms are still in development stage, functional interfaces have been reserved but optimization effects are limited
- **Existing Features**: Basic segment merging and path simplification have been implemented, but optimization effects for complex routing scenarios are not ideal
- **Future Plans**: Will improve optimization algorithms in future versions to enhance path quality and routing efficiency
- **Usage Suggestion**: Current version recommends focusing on routing correctness and completeness, optimization features can be used as auxiliary reference

#### Segment Merging

**Function**: Merges collinear path segments, removes redundant points

**Example**:
```
Before optimization: (0,0) → (1,0) → (2,0) → (3,0)
After optimization: (0,0) → (3,0)
```

**Current Status**: ✅ Basic functionality implemented, can effectively reduce collinear points

**Advantages**:
- Reduces number of path points
- Simplifies path representation
- Improves subsequent processing efficiency

#### Dogleg Removal

**Function**: Eliminates unnecessary turns, making paths more direct

**Example**:
```
Before optimization: (0,0) → (1,0) → (1,1) → (2,1)
After optimization: (0,0) → (0,1) → (2,1)  (if feasible)
```

**Current Status**: ⚠️ Interface reserved, but optimization effects limited, may not handle complex scenarios

**Advantages**:
- Reduces number of turns
- Shortens path length
- Improves routing aesthetics

#### Manhattan Shortcutting

**Function**: Finds shorter alternative paths within local ranges

**Working Principle**:
1. Detects local segments in paths
2. Attempts to replace with shorter Manhattan paths
3. Verifies new paths do not conflict with other paths
4. If valid, replaces original path segments

**Current Status**: ⚠️ Interface reserved, but optimization logic not yet complete, actual effects unstable

**Advantages**:
- Locally optimizes path length
- Maintains Manhattan style
- Avoids global conflicts

**Future Improvement Directions**:
- Enhance conflict detection mechanism
- Optimize path smoothing algorithms
- Support multi-objective optimization (length, turns, aesthetics)
- Provide configurable optimization strategies
- Add optimization effect evaluation metrics

### Snapshot Management System

The snapshot system supports nonlinear workflows, allowing free switching between different states.

#### Automatic Snapshot Creation

**Trigger Timing**:
- Automatically created after each area is completed
- Contains complete router state and all paths

**Snapshot Content**:
- Area number
- Creation timestamp
- Occupation grid state
- Diagonal bitmap
- All completed paths
- Global reserved points set

#### Snapshot Viewing

**Function**: View all saved snapshot information

**Display Content**:
- Snapshot number
- Area number
- Creation time
- Path count

**Operation**: Press `Ctrl+H` to open snapshot list dialog

#### Snapshot Switching

**Function**: Restore to any historical snapshot state

**Features**:
- Supports repeated switching (can switch back and forth between different snapshots)
- Automatically saves current work before switching
- Completely restores router state and all paths
- Supports nonlinear exploration (try different routing schemes)

**Usage Scenarios**:
- Compare different routing schemes
- Roll back to previous state for re-routing
- Explore multiple possibilities

**Operation**: Press `Ctrl+T` to open snapshot switching dialog

### Intelligent Boundary Matching

The system automatically analyzes boundary configurations and provides optimal connection strategies.

#### Boundary Detection

**Automatic Identification**:
- Detects boundaries where Center standby points are located
- Detects boundaries where Out standby points are located
- Determines boundary relationships (parallel/L-shaped)

**Boundary Definition**:
- **Top boundary**: Edge with maximum y-coordinate
- **Bottom boundary**: Edge with minimum y-coordinate
- **Left boundary**: Edge with minimum x-coordinate
- **Right boundary**: Edge with maximum x-coordinate

#### Strategy Recommendation

**Recommendation Logic**:
1. Analyzes point distribution characteristics
2. Calculates expected path lengths for each strategy
3. Evaluates potential conflict risks
4. Recommends optimal strategy

**User Selection**:
- Can accept system recommendation
- Can also manually select other strategies
- Real-time preview of different strategy effects

### Diagonal Occupancy Strategy

Intelligent spacing control mechanism to ensure routing meets minimum spacing requirements.

#### Working Principle

**Problem**: Diagonal paths may cause insufficient spacing
```
Example: Two diagonal paths crossing in the grid
  ╱ ╲
 ╱   ╲
╱     ╲
```

**Solution**: Diagonal occupancy strategy
1. When a diagonal path occupies a grid cell
2. Automatically mark the remaining two diagonally opposite grid points as occupied
3. Ensure subsequent paths do not come too close

**Parameter Settings**:
- Grid size: 15 units
- Minimum spacing requirement: ≥15 units
- Diagonal length: 15√2 ≈ 21.2 units

**Advantages**:
- No additional spacing detection required
- O(1) time complexity
- Automatically satisfies design rules

### GDS File Processing Tools

The system provides two fully integrated GDS file processing tools, supporting coordinate extraction from GDS files for routing, and materializing routing results and merging them back into GDS files.

#### Tool 1: GDS Coordinate Extraction Tool

**Function Overview**: Extracts rectangular coordinates of specified sizes from target GDS files, converts to grid coordinate system, and generates CSV files usable for system routing.

**Usage Scenarios**:
- Extract Out points, Center points, obstacles, etc. coordinates from existing GDS layouts
- Map physical coordinates to routing system's grid coordinates
- Batch process multiple types of rectangular shapes

**Main Features**:

1. **GDS File Loading**
   - Supports standard GDS II format files
   - Automatically identifies all Cells in the file
   - Displays available Cell list for selection

2. **Rectangle Configuration and Extraction**
   - Precisely matches rectangles by size (tolerance can be set)
   - Supports multiple label types: `out`, `center`, `obstacle`, `chip_range`
   - Supports multiple key point positions: center point, four corner points, all vertices
   - Direction filtering: can filter rectangles by up/down/left/right directions
   - Boundary restrictions: can set x/y coordinate range filtering

3. **Grid Mapping**
   - Maps physical coordinates to specified grid size
   - Automatically aligns to grid points
   - Supports custom grid size (default 15 units)

4. **Obstacle Processing**
   - Obstacle expansion: can set left/right/up/down expansion grid count
   - Special obstacles: automatically add obstacles between specified label points
   - Distance parameter control: set distance threshold for obstacle addition

5. **Visualization and Export**
   - Real-time visualization of extraction results
   - Displays grid lines and distribution of different types of points
   - Exports to CSV files (includes grid_x, grid_y, layer, direction and other fields)
   - Saves visualization images in PNG format

**Operation Flow**:
```
1. Select GDS file → Load file → View available Cells
   ↓
2. Add rectangle configuration (multiple can be added)
   - Select Cell name
   - Set label type (out/center/obstacle/chip_range)
   - Set rectangle size (width, height, tolerance)
   - Select key point position
   - (Optional) Enable direction filtering and boundary restrictions
   ↓
3. Set processing options
   - Grid size
   - (Optional) Obstacle expansion parameters
   - (Optional) Special obstacle processing
   ↓
4. Start extraction → View visualization results → Export CSV
```

**Output CSV Format**:
```csv
grid_x,grid_y,layer,direction,x,y
150.0,200.0,out,top,150.5,200.3
165.0,200.0,out,top,165.2,200.8
180.0,215.0,center,,180.0,215.0
195.0,230.0,obstacle,,195.0,230.0
```

**Access Method**:
- Menu bar: **Tools → GDS Coordinate Extraction**
- Shortcut: `Ctrl+G`

---

#### Tool 2: Path Materialization and Merging Tool

**Function Overview**: Converts system-generated routing data (PKL files) into materialized GDS paths and merges them into target GDS files, generating complete layouts containing routing results.

**Usage Scenarios**:
- Convert routing results into manufacturable GDS layouts
- Merge routing paths into existing chip designs
- Generate final layout files

**Main Features**:

1. **File Input**
   - **PKL File**: System-saved routing data (contains all path information)
   - **CSV File**: Original coordinate file (for grid coordinate to physical coordinate mapping)
   - **Target GDS File**: Original layout file that needs routing merged

2. **Coordinate Conversion**
   - Convert from grid coordinate system back to physical coordinate system
   - Use mapping relationships in CSV file to ensure precise coordinate correspondence
   - Automatically handle coordinate offsets and scaling

3. **Path Materialization**
   - Convert discrete path points to continuous GDS FlexPath
   - Supports diagonal paths and Manhattan paths
   - Can set path width (default 10 units)
   - Automatically handles path corners and connections

4. **GDS Parameter Configuration**
   - **Layer**: Specify GDS layer number for routing paths (default 31)
   - **Datatype**: Specify data type (default 0)
   - **Path Width**: Set physical width of routing
   - **Target Cell**: Specify Cell name to merge into

5. **Merging and Output**
   - Add all routing paths to target Cell
   - Keep other contents of original GDS file unchanged
   - Generate new GDS file (does not overwrite original)
   - Output to `data/output/gds/` directory

**Operation Flow**:
```
1. Select input files
   - PKL file (routing data)
   - CSV file (coordinate mapping)
   - Target GDS file (original layout)
   ↓
2. Set GDS parameters
   - Grid size (consistent with extraction)
   - Layer and Datatype
   - Path width
   - Target Cell name
   ↓
3. Start materialization and merging
   - Read PKL and CSV files
   - Convert path coordinates
   - Create GDS FlexPath
   - Merge to target GDS
   ↓
4. Save output file → View processing log
```

**Processing Flow Diagram**:
```
PKL file (grid coordinate paths)
    ↓
Coordinate conversion (using CSV mapping)
    ↓
Physical coordinate paths
    ↓
GDS FlexPath materialization
    ↓
Merge to target GDS Cell
    ↓
Output complete GDS file
```

**Access Method**:
- Menu bar: **Tools → Path Materialization and Merging**
- Shortcut: `Ctrl+M`

---

#### Complete Workflow

**Complete workflow from GDS to routing back to GDS**:

```
Step 1: GDS coordinate extraction
  Input: Original chip layout.gds
  Output: Coordinate data.csv
  ↓
Step 2: System routing
  Input: Coordinate data.csv
  Output: Routing results.pkl
  ↓
Step 3: Path materialization and merging
  Input: Routing results.pkl + Coordinate data.csv + Original chip layout.gds
  Output: Complete layout with routing.gds
```

**Notes**:
- Grid size used by both tools must be consistent
- CSV file plays a key role in coordinate mapping throughout the process
- It is recommended to use the same GDS file as the base for both extraction and merging
- Output GDS files will be saved to `data/output/gds/` directory

**Dependency Requirements**:
- Need to install `gdspy` library (optional dependency): `pip install "gdspy>=1.6.0,<2.0.0"`
- If not installed, the tool will prompt for installation command

---

## ❓ Frequently Asked Questions

### Installation Related

#### Q: What to do if pip install fails?

**A**: Try the following solutions:

```bash
# Method 1: Upgrade pip
python -m pip install --upgrade pip

# Method 2: Use domestic mirror source
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Method 3: Use Tsinghua mirror
pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

#### Q: Numba installation failed?

**A**: Numba is an optional dependency and does not affect core functionality

- The system will automatically use pure Python implementation
- Log will show: `[Warning] Numba not installed, using pure Python implementation`
- If acceleration is needed, you can try:
  ```bash
  # Install specific version
  pip install numba==0.56.4

  # Or skip Numba, system can still run normally
  ```

#### Q: tkinter module not found?

**A**: tkinter is a Python standard library, but some systems require separate installation

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install python3-tkinter

# macOS (using Homebrew)
brew install python-tk
```

### Usage Related

#### Q: No display after importing CSV?

**A**: Check CSV file format

1. **Required fields check**:
   - Ensure there are `x`, `y`, `layer` three columns
   - `direction` column is required for Out points to guide system automated routing strategy

2. **Data type check**:
   - `x` and `y` must be numbers
   - `layer` must be one of：`out`, `center`, `obstacle`, `chip_range`
   - `direction` must be one of：`top`, `bottom`, `left`, `right`

3. **Encoding check**:
   - Ensure CSV file uses UTF-8 encoding
   - Avoid direct editing with Excel (may cause encoding issues)

#### Q: What to do if routing fails?

**A**: Possible reasons and solutions

**Reason 1: Area selection too small**
- Solution: Expand polygon selection area to ensure sufficient routing space

**Reason 2: Too many obstacles**
- Solution: Check obstacle point distribution, adjust obstacle positions if necessary

**Reason 3: Mismatched number of points**
- Solution: Ensure Center point count matches or is close to Out point count

**Reason 4: Boundary points too dense**
- Solution: Use manual mode to distribute points to different boundaries

**Debugging methods**:
1. Check detailed error information in log panel
2. Use manual mode to precisely control point allocation
3. Try batch processing, complete routing for some points first

#### Q: How to view standby point numbers?

**A**: Three methods

**Method 1: Automatic prompt**
- After Stage 2 is completed, the system will pop up a dialog asking if you want to print labels
- Click "Yes" to view complete number summary

**Method 2: Canvas display**
- When number of points < 100, numbers will be automatically displayed on the canvas
- You can use canvas zoom function to view details

**Method 3: Log viewing**
- Log panel will output number information for all standby points
- You can scroll to view historical logs

#### Q: Will data be lost after snapshot switching?

**A**: No

- The system will automatically save current working state before switching
- You can switch back to previous states at any time
- Supports repeated switching between multiple snapshots

#### Q: How to select multiple points in manual mode?

**A**: Use right-click drag

1. **Hold down right mouse button**
2. **Drag mouse** to form selection box
3. **Release right mouse button** to complete selection
4. All points within the box will be selected
5. You can perform multiple box selections to accumulate selection

**Other selection methods**:
- Left-click: Select single point
- Ctrl+Z: Undo last selection
- Enter: Confirm current selection

### Performance Related

#### Q: What to do if it runs very slowly?

**A**: Performance optimization suggestions

**Optimization 1: Install Numba (optional dependency)**
```bash
pip install "numba>=0.55.0,<1.0.0"
# Can speed up 10-50 times
```

**Optimization 2: Adjust grid size**
- Edit `photonic_routing/config/constants.py`
- Increase `DEFAULT_GRID_SIZE` (default 15)
- Larger grid = fewer grid cells = faster speed

**Optimization 3: Batch processing**
- Divide large-scale data into multiple small areas
- Complete routing for each area individually
- Save snapshots after each area is completed

**Optimization 4: Reduce visualization updates**
- Minimize the window during routing
- View results after completion

#### Q: What to do if memory usage is high?

**A**: Memory management suggestions


1. Save and clean up promptly after completing areas
2. Unneeded snapshots can be deleted
3. Close unnecessary visualizations
4. Batch process large-scale data

**When memory is insufficient**:
- Save current work
- Restart the program
- Load saved data to continue working

#### Q: How to handle large-scale data?

**A**: Large-scale data processing strategy

**Strategy: Partition processing**
```
1. Divide the chip into multiple areas
2. Route each area independently
3. Merge results at the end
```

### Data Related

#### Q: What data formats are supported?

**A**: Supported formats

**Input formats**:
- CSV files (main format)
- GDS files (coordinates extracted via tools)
- PKL files (load previous work)

**Output formats**:
- PKL files (complete working state)
- PNG images (visualization results)
- GDS files (exported via tools)


### Interface Related

#### Q: Interface display incomplete?

**A**: Adjust display settings

**Method 1: Adjust window size**
- Maximize the window
- Or manually adjust to appropriate size

**Method 2: Use scroll functionality**
- Control panel supports mouse wheel scrolling
- Can view all controls

**Method 3: Adjust DPI settings**
- Windows system: Adjust display scaling
- Recommended to use 100% or 125% scaling

#### Q: Canvas cannot be zoomed?

**A**: Use Matplotlib toolbar

- There is a Matplotlib toolbar at the bottom of the canvas
- Click the magnifier icon to enable zoom mode
- Click the cross icon to enable pan mode
- Click the Home icon to restore original view

#### Q: Too many log messages to see clearly?

**A**: Log management

- Log panel supports scrolling
- Can copy log content to text editor
- Different log levels have color distinctions:
  - Green: Success information
  - Gray: Normal information
  - Yellow: Warning information
  - Red: Error information

---

## 📝 Update Log

### v0.0.0 (Current Version)

**Core Features** ✅

- ✅ Three-stage routing process (Out internal → Center internal → External connection)
- ✅ DiagonalBitmap O(1) diagonal collision detection
- ✅ 8-direction A* algorithm path search (supports diagonal movement)
- ✅ Diagonal occupancy strategy (intelligent spacing control)
- ✅ Numba JIT acceleration (optional, 10-50x speedup)

**Path Optimization** ⚠️

- ⚠️ Segment merging algorithm (basic functionality implemented)
- ⚠️ Dogleg removal algorithm (interface reserved, limited effect)
- ⚠️ Manhattan shortcut optimization (interface reserved, logic to be improved)
- ⚠️ Automatic path simplification (basic functionality available)
- **Note**: Path optimization features are still in development stage, current version has limited optimization effects, future versions will continue to improve

**User Interface** ✅

- ✅ Light blue and white professional theme
- ✅ Scrollable control panel (adaptive layout)
- ✅ Real-time logging system (graded color output)
- ✅ Matplotlib high-quality visualization
- ✅ Interactive canvas (polygon selection, clicking, box selection)

**Data Management** ✅

- ✅ CSV data import (supports direction field)
- ✅ PKL data persistence
- ✅ GDS file support (extraction and export)
- ✅ Unified path management system
- ✅ Automatic directory creation

**Snapshot System** ✅

- ✅ Automatic snapshot creation (after each region completion)
- ✅ Snapshot viewing functionality
- ✅ Snapshot switching functionality (supports repeated switching)
- ✅ Non-linear workflow support

**Boundary Matching** ✅

- ✅ Automatic boundary type detection (parallel/L-shaped)
- ✅ 4 mapping strategies (for each boundary type)
- ✅ Intelligent strategy recommendation
- ✅ Manual strategy selection

**Operation Modes** ✅

- ✅ Auto mode (intelligent allocation and routing)
- ✅ Manual mode (precise control)
- ✅ Hybrid mode (flexible switching)

**Known Limitations** ⚠️

- ⚠️ Large-scale data performance needs optimization
- ⚠️ Some extremely complex layouts may require manual intervention
- ⚠️ **GDS file processing functionality requires installation of gdspy library (optional dependency)**: `pip install "gdspy>=1.6.0,<2.0.0"`
- ⚠️ **Performance optimization requires installation of numba library (optional dependency)**: `pip install "numba>=0.55.0,<1.0.0"`
- ⚠️ **Path optimization algorithm is not yet complete**: The current version's path optimization features (segment merging, dogleg removal, Manhattan shortcuts) only provide basic interfaces with limited optimization effects and cannot effectively handle complex routing scenarios. Future versions will focus on improvements

**Planned Features** 🔮

- 🔮 Complete path optimization algorithm (high priority)
- 🔮 Multi-threaded parallel routing
- 🔮 Routing quality evaluation tool
- 🔮 Batch processing mode
- 🔮 Configuration file support
- 🔮 Optimize GDS file processing functionality

---

## 👥 Contribution and Support

### Contribution Guide

Welcome to contribute code, report issues, or suggest improvements!

**How to contribute**:
1. Fork this project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Issue Reporting

If you encounter issues or have suggestions, please report them through the following channels:

- **GitHub Issues**: Submit detailed issue descriptions
- **Email contact**: [1277708896@qq.com]

**Please include when reporting**:
- System environment (OS, Python version)
- Error messages or screenshots
- Reproduction steps
- Relevant data files (if possible)

### Development Team

**EDA-Q Team**

- Project maintainer: [aknbg1thub]
- Core developer: [aknbg1thub]

### License

This project adopts the **GPL-3.0** license. See the [LICENSE](LICENSE) file for details.

---

## 📚 Related Resources



### Related Projects

- [gdspy](https://github.com/heitzmann/gdspy) - GDS file processing library
- [NetworkX](https://networkx.org/) - Graph theory algorithm library

### Academic Citation

If this project is helpful for your research, please cite:

```bibtex
@software{photonic_quantum_chip_routing,
  title = {Photonic Quantum Chip Routing System},
  author = {EDA-Q Team},
  year = {2026},
  url = {https://github.com/Q-transmon-xmon/EDA-Q/photonic_quantum_chip}
}
```

---

<div align="center">

**Thank you for using the Photonic Quantum Chip Routing System!**

If you have any questions or suggestions, please feel free to contact us at any time.

[⬆ Back to Top](#-photonic_quantum_chip-system)

</div>
