import streamlit as st
import random
import copy

st.set_page_config(page_title="Juanca Game - Tetris", page_icon=None, layout="centered")

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
    "I": "#00f0f0", "O": "#f0f000", "T": "#a000f0",
    "S": "#00f000", "Z": "#f00000", "J": "#0000f0", "L": "#f0a000",
}

COLOR_INDEX = {name: i + 1 for i, name in enumerate(COLORS)}
INDEX_COLOR = {v: COLORS[k] for k, v in COLOR_INDEX.items()}

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
        do_action("down")

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

def render_board_html(board, piece):
    display = copy.deepcopy(board)
    if not st.session_state.game_over:
        ghost_row = get_ghost_row(board, piece)
        for r, row in enumerate(piece["shape"]):
            for c, cell in enumerate(row):
                if cell:
                    gr = ghost_row + r
                    gc = piece["col"] + c
                    if 0 <= gr < ROWS and 0 <= gc < COLS and display[gr][gc] == EMPTY:
                        display[gr][gc] = -1
        for r, row in enumerate(piece["shape"]):
            for c, cell in enumerate(row):
                if cell:
                    pr = piece["row"] + r
                    pc = piece["col"] + c
                    if 0 <= pr < ROWS and 0 <= pc < COLS:
                        display[pr][pc] = piece["color_idx"]
    cs = 30
    g = 2
    w = COLS * (cs + g) + g
    h = ROWS * (cs + g) + g
    cells = []
    for r in range(ROWS):
        for c in range(COLS):
            x = g + c * (cs + g)
            y = g + r * (cs + g)
            v = display[r][c]
            if v == -1:
                stroke = INDEX_COLOR.get(piece["color_idx"], "#555")
                cells.append(f'<rect x="{x}" y="{y}" width="{cs}" height="{cs}" fill="#222" fill-opacity="0.4" stroke="{stroke}" stroke-width="1.5" rx="4"/>')
            elif v == EMPTY:
                cells.append(f'<rect x="{x}" y="{y}" width="{cs}" height="{cs}" fill="#111827" stroke="#1e293b" stroke-width="1" rx="4"/>')
            else:
                color = INDEX_COLOR.get(v, "#888")
                cells.append(f'<rect x="{x}" y="{y}" width="{cs}" height="{cs}" fill="{color}" stroke="rgba(255,255,255,0.1)" stroke-width="1" rx="4"/>')
                cells.append(f'<rect x="{x+3}" y="{y+3}" width="{cs//2-2}" height="{cs//2-2}" fill="rgba(255,255,255,0.2)" rx="2"/>')
    return f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a;border-radius:12px;border:2px solid #334155;box-shadow:0 0 30px rgba(0,240,240,0.1);">{"".join(cells)}</svg>'

def render_next(piece):
    shape = piece["shape"]
    rows, cols = len(shape), len(shape[0])
    cs, g = 24, 2
    w = cols * (cs + g) + g
    h = rows * (cs + g) + g
    color = COLORS[piece["name"]]
    cells = []
    for r in range(rows):
        for c in range(cols):
            x = g + c * (cs + g)
            y = g + r * (cs + g)
            if shape[r][c]:
                cells.append(f'<rect x="{x}" y="{y}" width="{cs}" height="{cs}" fill="{color}" stroke="rgba(255,255,255,0.15)" stroke-width="1" rx="4"/>')
            else:
                cells.append(f'<rect x="{x}" y="{y}" width="{cs}" height="{cs}" fill="#111827" stroke="#1e293b" stroke-width="1" rx="3"/>')
    return f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a;border-radius:8px;">{"".join(cells)}</svg>'

# ââ Styles ââ
st.markdown("""<style>
.stApp{background:#020617}
h1,h2,h3,p,span,div,label{color:#e2e8f0 !important}
.title{text-align:center;font-size:2.8rem;font-weight:900;background:linear-gradient(135deg,#06b6d4,#8b5cf6,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0.5rem 0 1rem;letter-spacing:2px}
.subtitle{text-align:center;color:#64748b !important;font-size:0.85rem;letter-spacing:4px;text-transform:uppercase;margin-bottom:1.5rem}
.stat{background:linear-gradient(145deg,#1e293b,#0f172a);border:1px solid #334155;border-radius:14px;padding:14px 18px;margin:8px 0;text-align:center}
.stat-label{font-size:0.7rem;color:#64748b !important;text-transform:uppercase;letter-spacing:3px;margin-bottom:4px}
.stat-val{font-size:1.8rem;font-weight:800;background:linear-gradient(135deg,#06b6d4,#22d3ee);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.go{text-align:center;font-size:2.2rem;font-weight:900;color:#ef4444 !important;text-shadow:0 0 30px #ef4444;animation:glow 1.5s ease-in-out infinite alternate}
@keyframes glow{from{text-shadow:0 0 10px #ef4444}to{text-shadow:0 0 40px #ef4444,0 0 60px #ef444466}}
.hint{text-align:center;color:#475569 !important;font-size:0.75rem;margin-top:10px;letter-spacing:1px}
.stButton>button{background:linear-gradient(145deg,#1e293b,#0f172a) !important;color:#e2e8f0 !important;border:1px solid #334155 !important;border-radius:10px !important;font-size:1.1rem !important;font-weight:700 !important;padding:10px 0 !important;width:100% !important;transition:all 0.2s !important;letter-spacing:1px}
.stButton>button:hover{border-color:#06b6d4 !important;box-shadow:0 0 15px rgba(6,182,212,0.3) !important;transform:translateY(-1px) !important}
.stButton>button:active{transform:scale(0.97) !important}
</style>""", unsafe_allow_html=True)

st.markdown('<div class="title">JUANCA GAME</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Classic Tetris</div>', unsafe_allow_html=True)

# ââ Start / Game Over ââ
if not st.session_state.started or st.session_state.game_over:
    col = st.columns([1, 2, 1])[1]
    with col:
        if st.session_state.game_over:
            st.markdown('<div class="go">GAME OVER</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat"><div class="stat-label">Final Score</div><div class="stat-val">{st.session_state.score}</div></div>', unsafe_allow_html=True)
            st.markdown("")
        if st.button("NEW GAME" if st.session_state.game_over else "START GAME", use_container_width=True):
            init_state()
            st.rerun()
    st.stop()

# ââ Game Layout ââ
left, right = st.columns([3, 1.3])

with left:
    st.markdown(render_board_html(st.session_state.board, st.session_state.piece), unsafe_allow_html=True)
    st.markdown("")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("LEFT", key="bl"):
            do_action("left"); st.rerun()
    with c2:
        if st.button("RIGHT", key="br"):
            do_action("right"); st.rerun()
    with c3:
        if st.button("ROTATE", key="brot"):
            do_action("rotate"); st.rerun()
    with c4:
        if st.button("DOWN", key="bd"):
            do_action("down"); st.rerun()
    with c5:
        if st.button("DROP", key="bdrop"):
            do_action("drop"); st.rerun()
    st.markdown('<div class="hint">LEFT - RIGHT - ROTATE - DOWN - DROP</div>', unsafe_allow_html=True)

with right:
    st.markdown(f'<div class="stat"><div class="stat-label">Score</div><div class="stat-val">{st.session_state.score}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat"><div class="stat-label">Level</div><div class="stat-val">{st.session_state.level}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat"><div class="stat-label">Lines</div><div class="stat-val">{st.session_state.lines}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="stat"><div class="stat-label">Next</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="display:flex;justify-content:center;margin-top:4px">{render_next(st.session_state.next_piece)}</div>', unsafe_allow_html=True)
    st.markdown("")
    if st.button("RESTART", key="restart"):
        init_state()
        st.rerun()

speed = max(300, 1100 - st.session_state.level * 80)
st.markdown(f"""<script>
setTimeout(function(){{var b=window.parent.document.querySelectorAll('button');for(var i=0;i<b.length;i++){{if(b[i].innerText==='DOWN'){{b[i].click();break}}}}}},{speed});
(function(){{
  var d=window.parent.document;
  if(!d._tetrisKeys){{
    d._tetrisKeys=true;
    d.addEventListener('keydown',function(e){{
      var map={{'ArrowLeft':'LEFT','ArrowRight':'RIGHT','ArrowUp':'ROTATE','ArrowDown':'DOWN',' ':'DROP'}};
      var t=map[e.key];
      if(t){{
        e.preventDefault();
        var b=d.querySelectorAll('button');
        for(var i=0;i<b.length;i++){{if(b[i].innerText===t){{b[i].click();break}}}}
      }}
    }});
  }}
}})();
</script>""", unsafe_allow_html=True)
