import streamlit as st
import random
import json
import copy
import time

# âââ Page config âââ
st.set_page_config(page_title="Juanca Game", page_icon="ð®", layout="centered")

# âââ Constants âââ
COLS = 10
ROWS = 20
EMPTY = 0

SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}

COLORS = {
    "I": "#00f0f0",
    "O": "#f0f000",
    "T": "#a000f0",
    "S": "#00f000",
    "Z": "#f00000",
    "J": "#0000f0",
    "L": "#f0a000",
}

COLOR_INDEX = {name: i + 1 for i, name in enumerate(COLORS)}
INDEX_COLOR = {v: COLORS[k] for k, v in COLOR_INDEX.items()}

# âââ Game state helpers âââ
def new_board():
    return [[EMPTY] * COLS for _ in range(ROWS)]

def new_piece():
    name = random.choice(list(SHAPES.keys()))
    shape = copy.deepcopy(SHAPES[name])
    col = COLS // 2 - len(shape[0]) // 2
    return {"name": name, "shape": shape, "row": 0, "col": col, "color_idx": COLOR_INDEX[name]}

def rotate_shape(shape):
    return [list(row) for row in zip(*shape[::-1])]

def valid_position(board, piece, adj_row=0, adj_col=0, new_shape=None):
    shape = new_shape if new_shape else piece["shape"]
    for r, row in enumerate(shape):
        for c, cell in enumerate(row):
            if cell:
                nr = piece["row"] + r + adj_row
                nc = piece["col"] + c + adj_col
                if nr < 0 or nr >= ROWS or nc < 0 or nc >= COLS:
                    return False
                if board[nr][nc] != EMPTY:
                    return False
    return True

def lock_piece(board, piece):
    for r, row in enumerate(piece["shape"]):
        for c, cell in enumerate(row):
            if cell:
                board[piece["row"] + r][piece["col"] + c] = piece["color_idx"]

def clear_lines(board):
    cleared = 0
    new_board_rows = []
    for row in board:
        if all(cell != EMPTY for cell in row):
            cleared += 1
        else:
            new_board_rows.append(row)
    for _ in range(cleared):
        new_board_rows.insert(0, [EMPTY] * COLS)
    return new_board_rows, cleared

SCORE_TABLE = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}

def init_state():
    st.session_state.board = new_board()
    st.session_state.piece = new_piece()
    st.session_state.next_piece = new_piece()
    st.session_state.score = 0
    st.session_state.level = 1
    st.session_state.lines = 0
    st.session_state.game_over = False
    st.session_state.started = True

# âââ Initialize state âââ
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.game_over = False
    st.session_state.score = 0

def do_action(action):
    if st.session_state.game_over or not st.session_state.started:
        return
    board = st.session_state.board
    piece = st.session_state.piece

    if action == "left":
        if valid_position(board, piece, adj_col=-1):
            piece["col"] -= 1
    elif action == "right":
        if valid_position(board, piece, adj_col=1):
            piece["col"] += 1
    elif action == "rotate":
        rotated = rotate_shape(piece["shape"])
        if valid_position(board, piece, new_shape=rotated):
            piece["shape"] = rotated
        # Wall kick attempts
        elif valid_position(board, piece, adj_col=1, new_shape=rotated):
            piece["col"] += 1
            piece["shape"] = rotated
        elif valid_position(board, piece, adj_col=-1, new_shape=rotated):
            piece["col"] -= 1
            piece["shape"] = rotated
    elif action == "down":
        if valid_position(board, piece, adj_row=1):
            piece["row"] += 1
        else:
            lock_piece(board, piece)
            board, cleared = clear_lines(board)
            st.session_state.board = board
            st.session_state.lines += cleared
            st.session_state.score += SCORE_TABLE.get(cleared, 800)
            st.session_state.level = st.session_state.lines // 10 + 1
            st.session_state.piece = st.session_state.next_piece
            st.session_state.next_piece = new_piece()
            if not valid_position(st.session_state.board, st.session_state.piece):
                st.session_state.game_over = True
    elif action == "drop":
        while valid_position(board, piece, adj_row=1):
            piece["row"] += 1
        do_action("down")  # lock it

def get_ghost_row(board, piece):
    ghost_row = piece["row"]
    while True:
        ok = True
        for r, row in enumerate(piece["shape"]):
            for c, cell in enumerate(row):
                if cell:
                    nr = ghost_row + 1 + r
                    nc = piece["col"] + c
                    if nr >= ROWS or nc < 0 or nc >= COLS or board[nr][nc] != EMPTY:
                        ok = False
                        break
            if not ok:
                break
        if ok:
            ghost_row += 1
        else:
            break
    return ghost_row

def render_board_html(board, piece, show_ghost=True):
    display = copy.deepcopy(board)

    # Ghost piece
    if show_ghost and not st.session_state.game_over:
        ghost_row = get_ghost_row(board, piece)
        for r, row in enumerate(piece["shape"]):
            for c, cell in enumerate(row):
                if cell:
                    gr = ghost_row + r
                    gc = piece["col"] + c
                    if 0 <= gr < ROWS and 0 <= gc < COLS and display[gr][gc] == EMPTY:
                        display[gr][gc] = -1  # ghost marker

    # Active piece
    if not st.session_state.game_over:
        for r, row in enumerate(piece["shape"]):
            for c, cell in enumerate(row):
                if cell:
                    pr = piece["row"] + r
                    pc = piece["col"] + c
                    if 0 <= pr < ROWS and 0 <= pc < COLS:
                        display[pr][pc] = piece["color_idx"]

    cell_size = 28
    gap = 1
    width = COLS * (cell_size + gap) + gap
    height = ROWS * (cell_size + gap) + gap

    svg_cells = []
    for r in range(ROWS):
        for c in range(COLS):
            x = gap + c * (cell_size + gap)
            y = gap + r * (cell_size + gap)
            val = display[r][c]
            if val == -1:
                color = "#333333"
                opacity = "0.5"
                stroke = INDEX_COLOR.get(piece["color_idx"], "#555")
                svg_cells.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                    f'fill="{color}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="1" rx="3"/>'
                )
            elif val == EMPTY:
                svg_cells.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                    f'fill="#1a1a2e" stroke="#16213e" stroke-width="1" rx="3"/>'
                )
            else:
                color = INDEX_COLOR.get(val, "#888")
                svg_cells.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                    f'fill="{color}" stroke="#ffffff22" stroke-width="1" rx="3"/>'
                )
                # Shine effect
                svg_cells.append(
                    f'<rect x="{x+2}" y="{y+2}" width="{cell_size//2-2}" height="{cell_size//2-2}" '
                    f'fill="#ffffff" fill-opacity="0.15" rx="2"/>'
                )

    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg"
                style="background:#0f0f23; border-radius:8px; border:2px solid #333;">
                {"".join(svg_cells)}
             </svg>'''
    return svg

def render_next_piece_html(piece):
    shape = piece["shape"]
    rows = len(shape)
    cols = len(shape[0])
    cell_size = 22
    gap = 1
    w = cols * (cell_size + gap) + gap
    h = rows * (cell_size + gap) + gap
    color = COLORS[piece["name"]]

    cells = []
    for r in range(rows):
        for c in range(cols):
            x = gap + c * (cell_size + gap)
            y = gap + r * (cell_size + gap)
            if shape[r][c]:
                cells.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                    f'fill="{color}" stroke="#ffffff22" stroke-width="1" rx="3"/>'
                )
            else:
                cells.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
                    f'fill="#1a1a2e" stroke="#16213e" stroke-width="1" rx="2"/>'
                )

    svg = f'''<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg"
                style="background:#0f0f23; border-radius:6px;">
                {"".join(cells)}
             </svg>'''
    return svg


# âââââââââââââ UI âââââââââââââ

st.markdown("""
<style>
    .stApp { background-color: #0a0a1a; }
    h1, h2, h3, p, span, div, label { color: #e0e0ff !important; }
    .game-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00f0f0, #a000f0, #f0a000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .score-box {
        background: #16213e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 6px 0;
        text-align: center;
    }
    .score-label { font-size: 0.75rem; color: #888 !important; text-transform: uppercase; letter-spacing: 2px; }
    .score-value { font-size: 1.5rem; font-weight: 700; color: #00f0f0 !important; }
    .game-over-text {
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
        color: #f00 !important;
        text-shadow: 0 0 20px #f00;
        animation: pulse 1s infinite;
    }
    @keyframes pulse { 50% { opacity: 0.5; } }
    .controls-hint {
        text-align: center;
        color: #666 !important;
        font-size: 0.8rem;
        margin-top: 8px;
    }
    /* Style buttons */
    .stButton > button {
        background: #16213e !important;
        color: #e0e0ff !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        font-size: 1.3rem !important;
        padding: 8px 0 !important;
        width: 100% !important;
        transition: all 0.15s !important;
    }
    .stButton > button:hover {
        background: #1a1a4e !important;
        border-color: #00f0f0 !important;
        box-shadow: 0 0 10px #00f0f044 !important;
    }
    .stButton > button:active {
        transform: scale(0.95) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="game-title">ð® JUANCA GAME</div>', unsafe_allow_html=True)

# âââ Start / Restart âââ
if not st.session_state.started or st.session_state.game_over:
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        if st.session_state.game_over:
            st.markdown('<div class="game-over-text">GAME OVER</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="score-box"><span class="score-label">Final Score</span><br>'
                f'<span class="score-value">{st.session_state.score}</span></div>',
                unsafe_allow_html=True,
            )
        if st.button("ð® New Game" if st.session_state.game_over else "â¶ï¸ Start Game", use_container_width=True):
            init_state()
            st.rerun()
    st.stop()

# âââ Main game layout âââ
board_col, side_col = st.columns([3, 1.2])

with board_col:
    svg = render_board_html(st.session_state.board, st.session_state.piece)
    st.markdown(svg, unsafe_allow_html=True)

    # Controls row
    st.markdown("")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("â¬ï¸", key="bl"):
            do_action("left"); st.rerun()
    with c2:
        if st.button("â¡ï¸", key="br"):
            do_action("right"); st.rerun()
    with c3:
        if st.button("ð", key="brot"):
            do_action("rotate"); st.rerun()
    with c4:
        if st.button("â¬ï¸", key="bd"):
            do_action("down"); st.rerun()
    with c5:
        if st.button("â¬", key="bdrop"):
            do_action("drop"); st.rerun()

    st.markdown('<div class="controls-hint">â¬ï¸ Left Â· â¡ï¸ Right Â· ð Rotate Â· â¬ï¸ Down Â· â¬ Hard Drop</div>', unsafe_allow_html=True)

with side_col:
    # Score
    st.markdown(
        f'<div class="score-box"><span class="score-label">Score</span><br>'
        f'<span class="score-value">{st.session_state.score}</span></div>',
        unsafe_allow_html=True,
    )
    # Level
    st.markdown(
        f'<div class="score-box"><span class="score-label">Level</span><br>'
        f'<span class="score-value">{st.session_state.level}</span></div>',
        unsafe_allow_html=True,
    )
    # Lines
    st.markdown(
        f'<div class="score-box"><span class="score-label">Lines</span><br>'
        f'<span class="score-value">{st.session_state.lines}</span></div>',
        unsafe_allow_html=True,
    )
    # Next piece
    st.markdown(
        '<div class="score-box"><span class="score-label">Next</span><br></div>',
        unsafe_allow_html=True,
    )
    next_svg = render_next_piece_html(st.session_state.next_piece)
    st.markdown(f'<div style="display:flex;justify-content:center;">{next_svg}</div>', unsafe_allow_html=True)

    st.markdown("")
    if st.button("ð Restart", key="restart"):
        init_state()
        st.rerun()

# Auto-drop with autorefresh
speed = max(0.3, 1.1 - st.session_state.level * 0.08)
st.markdown(
    f"""
    <script>
        setTimeout(function() {{
            // Find and click the down button
            const buttons = window.parent.document.querySelectorAll('button');
            for (const btn of buttons) {{
                if (btn.innerText.includes('â¬ï¸')) {{
                    btn.click();
                    break;
                }}
            }}
        }}, {int(speed * 1000)});
    </script>
    """,
    unsafe_allow_html=True,
)
