
# dames_game_mobile_v2.py
import random
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen

TAILLE = 8

# 0=vide, 1=pion1, 2=pion2, 3=dame1, 4=dame2

class Case(Widget):
    def __init__(self, row, col, base_color, **kwargs):
        super().__init__(**kwargs)
        self.row = row
        self.col = col
        self.base_color = base_color
        self.value = 0
        self.hl_alpha = 0.0
        self.hl_anim = None
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *a):
        self.canvas.clear()
        with self.canvas:
            Color(*self.base_color)
            Rectangle(pos=self.pos, size=self.size)
            if self.value in (1,2,3,4):
                Color(0.0,0.7,0.0) if self.value in (1,3) else Color(0.8,0,0)
                pad = min(self.width,self.height)*0.12
                Ellipse(pos=(self.x+pad, self.y+pad), size=(self.width-2*pad,self.height-2*pad))
                if self.value in (3,4):
                    Color(1,1,1)
                    inner_pad = min(self.width,self.height)*0.28
                    Ellipse(pos=(self.x+inner_pad,self.y+inner_pad), size=(self.width-2*inner_pad,self.height-2*inner_pad))
            if self.hl_alpha > 0:
                Color(1,1,0,self.hl_alpha)
                Rectangle(pos=self.pos, size=self.size)

    def start_highlight(self):
        self.stop_highlight()
        self.hl_anim = Animation(hl_alpha=0.45, duration=0.35) + Animation(hl_alpha=0.05, duration=0.35)
        self.hl_anim.repeat = True
        self.hl_anim.start(self)

    def stop_highlight(self):
        if self.hl_anim:
            try: self.hl_anim.cancel(self)
            except: pass
            self.hl_anim=None
        self.hl_alpha=0
        self._redraw()

class DameGame(BoxLayout):
    def __init__(self, mode="pvp", manager=None, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.mode = mode
        self.manager = manager
        self.current_player = 1
        self.board = [[0]*TAILLE for _ in range(TAILLE)]
        self.cases = {}
        self.selected = None
        self.possible_targets = []
        self.bot_thinking = False

        self.status = Label(text="", bold=True, size_hint_y=None, height=50)
        self.add_widget(self.status)

        self.grid = GridLayout(cols=TAILLE, rows=TAILLE, spacing=0)
        self.add_widget(self.grid)

        bottom = BoxLayout(size_hint_y=None, height=60, spacing=10, padding=10)
        btn_reset = Button(text="Recommencer", on_press=self.go_to_menu)
        bottom.add_widget(btn_reset)
        self.add_widget(bottom)

        self._create_board()
        self._place_initial_pieces()
        self.highlight_playable_pawns()
        self.update_ui()
        self.update_status()

    # --------------------------
    # Board & UI
    # --------------------------
    def _create_board(self):
        self.grid.clear_widgets()
        self.cases.clear()
        for r in range(TAILLE):
            for c in range(TAILLE):
                base_color = (0.95,0.95,0.95,1) if (r+c)%2==0 else (0.18,0.18,0.18,1)
                case = Case(r,c,base_color,size_hint=(1,1))
                self.grid.add_widget(case)
                self.cases[(r,c)] = case

    def _place_initial_pieces(self):
        for r in range(TAILLE):
            for c in range(TAILLE):
                self.board[r][c]=0
                self.cases[(r,c)].value=0
        for r in range(3):
            for c in range(TAILLE):
                if (r+c)%2==1:
                    self.board[r][c]=1
                    self.cases[(r,c)].value=1
        for r in range(5,8):
            for c in range(TAILLE):
                if (r+c)%2==1:
                    self.board[r][c]=2
                    self.cases[(r,c)].value=2

    def update_ui(self):
        for (r,c), case in self.cases.items():
            case.value = self.board[r][c]
            case._redraw()
        self.update_status()

    def update_status(self):
        cnt1 = sum(1 for r in range(TAILLE) for c in range(TAILLE) if self.board[r][c] in (1,3))
        cnt2 = sum(1 for r in range(TAILLE) for c in range(TAILLE) if self.board[r][c] in (2,4))
        player_has_moves = bool(self.get_all_possible_moves(self.current_player))
        if cnt1==0 or (self.current_player==1 and not player_has_moves):
            self.status.text="Le joueur 2 (ROUGE) a gagné !"
            self.stop_all_highlights()
            return
        if cnt2==0 or (self.current_player==2 and not player_has_moves):
            self.status.text="Le joueur 1 (VERT) a gagné !"
            self.stop_all_highlights()
            return
        self.status.text=f"Tour joueur {self.current_player} ({'VERT' if self.current_player==1 else 'ROUGE'})"

    # --------------------------
    # Input
    # --------------------------
    def on_touch_down(self, touch):
        if self.bot_thinking: return True
        for (r,c), case in self.cases.items():
            if case.collide_point(*touch.pos):
                self.handle_click(r,c)
                return True
        return super().on_touch_down(touch)

    def handle_click(self,r,c):
        val=self.board[r][c]
        if self.selected is None:
            if val!=0 and self.is_own_piece(val,self.current_player):
                moves,_=self.get_moves_for_piece(r,c)
                global_caps=self.get_all_captures(self.current_player)
                if global_caps: moves=[m for m in moves if m[2] is not None]
                if moves:
                    self.selected=(r,c)
                    self.possible_targets=moves
                    # arrêter les pions clignotants
                    for rr in range(TAILLE):
                        for cc in range(TAILLE):
                            if self.is_own_piece(self.board[rr][cc], self.current_player):
                                self.cases[(rr,cc)].stop_highlight()
                    # clignoter les cases de destination
                    for tr,tc,_ in moves:
                        self.cases[(tr,tc)].start_highlight()
                else:
                    self.show_temp_message("Aucun coup possible pour ce pion.")
            else:
                self.show_temp_message("Cliquez sur un pion à vous pour sélectionner.")
        else:
            sr,sc=self.selected
            found=None
            for tr,tc,cap in self.possible_targets:
                if tr==r and tc==c: found=(tr,tc,cap); break
            if found:
                tr,tc,capinfo=found
                self.execute_move(sr,sc,tr,tc,capinfo)
                self.stop_all_highlights()
                more_caps=self.get_capture_moves_from(tr,tc) if capinfo else []
                if more_caps:
                    # reste sélectionné si encore captures
                    self.selected=(tr,tc)
                    self.possible_targets=[(nr,nc,[(mr,mc)]) for nr,nc,mr,mc in more_caps]
                    for nr,nc,_ in self.possible_targets: self.cases[(nr,nc)].start_highlight()
                    self.update_ui()
                    return
                self.selected=None
                self.possible_targets=[]
                self.update_ui()
                self.check_promotion(tr,tc)
                self.switch_turn()
                if self.mode=="pve" and self.current_player==2:
                    Clock.schedule_once(lambda dt:self.bot_move(),0.25)
            else:
                self.selected=None
                self.possible_targets=[]
                self.stop_all_highlights()
                self.update_ui()
                self.highlight_playable_pawns()

    # --------------------------
    # Règles
    # --------------------------
    def is_own_piece(self,val,player): return val in (1,3) if player==1 else val in (2,4)

    def get_moves_for_piece(self,r,c):
        val=self.board[r][c]
        moves=[]
        captures=[]
        is_king=val in (3,4)
        player=1 if val in (1,3) else 2
        dirs=[(-1,-1),(-1,1),(1,-1),(1,1)]
        if is_king:
            for dr,dc in dirs:
                nr,nc=r+dr,c+dc
                while 0<=nr<TAILLE and 0<=nc<TAILLE:
                    if self.board[nr][nc]==0: moves.append((nr,nc,None)); nr+=dr; nc+=dc; continue
                    if self.is_own_piece(self.board[nr][nc],player): break
                    jump_r,jump_c=nr+dr,nc+dc
                    while 0<=jump_r<TAILLE and 0<=jump_c<TAILLE:
                        if self.board[jump_r][jump_c]==0: captures.append((jump_r,jump_c,[(nr,nc)])); jump_r+=dr;jump_c+=dc; continue
                        else: break
                    break
        else:
            forward=1 if player==1 else -1
            for dc in (-1,1):
                nr,nc=r+forward,c+dc
                if 0<=nr<TAILLE and 0<=nc<TAILLE and self.board[nr][nc]==0: moves.append((nr,nc,None))
            for dr,dc in [(-2,-2),(-2,2),(2,-2),(2,2)]:
                nr,nc=r+dr,c+dc
                if 0<=nr<TAILLE and 0<=nc<TAILLE:
                    mid_r,mid_c=(r+nr)//2,(c+nc)//2
                    if self.board[nr][nc]==0 and self.board[mid_r][mid_c]!=0 and not self.is_own_piece(self.board[mid_r][mid_c],player):
                        captures.append((nr,nc,[(mid_r,mid_c)]))
        return moves+captures, captures

    def get_capture_moves_from(self,r,c):
        val=self.board[r][c]; is_king=val in (3,4); player=1 if val in (1,3) else 2
        res=[]
        dirs=[(-1,-1),(-1,1),(1,-1),(1,1)]
        if is_king:
            for dr,dc in dirs:
                nr,nc=r+dr,c+dc
                while 0<=nr<TAILLE and 0<=nc<TAILLE:
                    if self.board[nr][nc]==0: nr+=dr; nc+=dc; continue
                    if self.is_own_piece(self.board[nr][nc],player): break
                    jump_r,jump_c=nr+dr,nc+dc
                    while 0<=jump_r<TAILLE and 0<=jump_c<TAILLE:
                        if self.board[jump_r][jump_c]==0: res.append((jump_r,jump_c,nr,nc)); jump_r+=dr;jump_c+=dc; continue
                        else: break
                    break
        else:
            for dr,dc in [(-2,-2),(-2,2),(2,-2),(2,2)]:
                nr,nc=r+dr,c+dc
                if 0<=nr<TAILLE and 0<=nc<TAILLE:
                    mid_r,mid_c=(r+nr)//2,(c+nc)//2
                    if self.board[nr][nc]==0 and self.board[mid_r][mid_c]!=0 and not self.is_own_piece(self.board[mid_r][mid_c],player):
                        res.append((nr,nc,mid_r,mid_c))
        return res

    def get_all_captures(self,player):
        res=[]
        for r in range(TAILLE):
            for c in range(TAILLE):
                val=self.board[r][c]
                if self.is_own_piece(val,player):
                    _,caps=self.get_moves_for_piece(r,c)
                    for tr,tc,capinfo in caps: res.append((r,c,tr,tc,capinfo))
        return res

    def get_all_possible_moves(self,player):
        all_moves=[]
        for r in range(TAILLE):
            for c in range(TAILLE):
                if self.is_own_piece(self.board[r][c],player):
                    moves,_=self.get_moves_for_piece(r,c)
                    if moves: all_moves.append((r,c,moves))
        return all_moves

    def execute_move(self,sr,sc,tr,tc,capture_info):
        val=self.board[sr][sc]
        if capture_info:
            for mr,mc in capture_info: self.board[mr][mc]=0; self.cases[(mr,mc)].value=0
        self.board[tr][tc]=self.board[sr][sc]; self.board[sr][sc]=0
        self.cases[(tr,tc)].value=self.cases[(sr,sc)].value; self.cases[(sr,sc)].value=0
        self.update_ui()

    def check_promotion(self,r,c):
        val=self.board[r][c]
        if val==1 and r==TAILLE-1: self.board[r][c]=3; self.cases[(r,c)].value=3; self.show_temp_message("Promotion en dame (joueur 1)")
        if val==2 and r==0: self.board[r][c]=4; self.cases[(r,c)].value=4; self.show_temp_message("Promotion en dame (joueur 2)")

    def switch_turn(self):
        self.current_player=2 if self.current_player==1 else 1
        self.update_status()
        self.stop_all_highlights()
        self.highlight_playable_pawns()

    def stop_all_highlights(self):
        for case in self.cases.values(): case.stop_highlight()

    def highlight_playable_pawns(self):
        if self.selected:
            return
        for r in range(TAILLE):
            for c in range(TAILLE):
                val = self.board[r][c]
                if self.is_own_piece(val, self.current_player):
                    moves,_ = self.get_moves_for_piece(r,c)
                    global_caps = self.get_all_captures(self.current_player)
                    if global_caps:
                        moves = [m for m in moves if m[2] is not None]
                    if moves:
                        self.cases[(r,c)].start_highlight()

    # --------------------------
    # Bot & messages
    # --------------------------
    def bot_move(self):
        if self.current_player!=2: return
        self.bot_thinking=True
        Clock.schedule_once(lambda dt:self._bot_think(),0.15)

    def _bot_think(self):
        all_caps=self.get_all_captures(2)
        if all_caps:
            f=random.choice(all_caps); fr,fc,tr,tc,capinfo=f
            self.execute_move(fr,fc,tr,tc,capinfo)
            while True:
                more=self.get_capture_moves_from(tr,tc)
                if not more: break
                choice=random.choice(more)
                ntr,ntc,mr,mc=choice
                self.execute_move(tr,tc,ntr,ntc,[(mr,mc)])
                tr,tc=ntr,ntc
            self.check_promotion(tr,tc)
            self.switch_turn()
            self.update_ui()
        else:
            all_moves=[]
            for r in range(TAILLE):
                for c in range(TAILLE):
                    if self.is_own_piece(self.board[r][c],2):
                        moves,_=self.get_moves_for_piece(r,c)
                        for tr,tc,capinfo in moves:
                            if not capinfo: all_moves.append((r,c,tr,tc))
            if all_moves:
                fr,fc,tr,tc=random.choice(all_moves)
                self.execute_move(fr,fc,tr,tc,None)
                self.check_promotion(tr,tc)
                self.switch_turn()
                self.update_ui()
        self.bot_thinking=False

    def show_temp_message(self,text,duration=1.5):
        old=self.status.text
        self.status.text=text
        Clock.unschedule(self._restore_status)
        Clock.schedule_once(lambda dt:self._restore_status(old),duration)
    def _restore_status(self,old_text): self.status.text=old_text

    def go_to_menu(self, instance=None):
        if self.manager: self.manager.current="menu"

# --------------------------
# Menu & screens
# --------------------------
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout=BoxLayout(orientation="vertical",padding=50,spacing=30)
        layout.add_widget(Label(text="Jeu de Dames",font_size=40))
        btn_pvp=Button(text="PvP",size_hint=(0.6,0.2),pos_hint={"center_x":0.5})
        btn_pve=Button(text="PvE",size_hint=(0.6,0.2),pos_hint={"center_x":0.5})
        btn_pvp.bind(on_press=lambda x:self.start_game("pvp"))
        btn_pve.bind(on_press=lambda x:self.start_game("pve"))
        layout.add_widget(btn_pvp); layout.add_widget(btn_pve)
        self.add_widget(layout)
    def start_game(self,mode):
        app=self.manager.app
        game_screen=DameScreen(mode=mode,name="game",manager=self.manager)
        self.manager.add_widget(game_screen)
        self.manager.current="game"

class DameScreen(Screen):
    def __init__(self, mode="pvp", manager=None, **kwargs):
        super().__init__(**kwargs)
        self.game = DameGame(mode=mode, manager=manager)
        self.add_widget(self.game)

class DameApp(App):
    def build(self):
        sm = ScreenManager()
        menu = MenuScreen(name="menu")
        sm.add_widget(menu)
        sm.app = self
        return sm

if __name__ == "__main__":
    DameApp().run()
