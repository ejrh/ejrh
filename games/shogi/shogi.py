#!/usr/bin/python

from pygame import *
import pygame
import pygame.draw as draw
import pygame.mixer as mixer
import pygame.sprite as FRG
import random
import ai
import game
from game import *

Font = None
LastKey = None

mixer.init(44100)
gong_sound = mixer.Sound('gong3.wav')
channel = gong_sound.play()

def computer_player(win):
    if game.current_player != 0:
        return
    
    def feedback(i, moves, depth):
        if depth == 3:
            win.blit(Font.render('%d/%d' % (i, moves), 1, (155, 155, 155), (0,0,0)), (475, 40))            
            display.flip()
            
    score, move = ai.evaluate_game(game, 2, feedback)
    if move is None:
        return
    slide_piece(win, game.get_current_player(), move)


def showtext(win, pos, text, color, bgcolor):
    textimg = Font.render(text, 1, color, bgcolor)
    win.blit(textimg, pos)
    return pos[0] + textimg.get_width() + 5, pos[1]


def drawbackground(win):
    win.fill((0,0,0))
    win.blit(Font.render('Shogi', 1, (155, 155, 155), (0,0,0)), (15, 15))
    
    if game.current_player == 0:
        colour1 = (255, 255, 255)
        colour2 = (155, 155, 155)
    else:
        colour1 = (155, 155, 155)
        colour2 = (255, 255, 255)
    
    win.blit(Font.render(game.players[0].name, 1, colour1, (0,0,0)), (475, 125))
    win.blit(Font.render(game.players[1].name, 1, colour2, (0,0,0)), (475, 380))
    
    if game.winner is not None:
        win.blit(Font.render(game.winner.name + ' wins', 1, colour2, (0,0,0)), (475, 250))    

    score = ai.evaluate_leaf(game)
    win.blit(Font.render('%0.1f' % score, 1, (155, 155, 155), (0,0,0)), (475, 15))

board_image_filename = 'shogi2.png'
piece_image_filenames = {
    'K': 'Shogi_osho.png',
    'R': 'Shogi_hisha.png',
    'B': 'Shogi_kakugyo.png',
    'G': 'Shogi_kinsho.png',
    'S': 'Shogi_ginsho.png',
    'N': 'Shogi_keima.png',
    'L': 'Shogi_kyosha.png',
    'P': 'Shogi_fuhyo.png',
    'k': 'Shogi_osho2.png',
    'r': 'Shogi_hisha2.png',
    'b': 'Shogi_kakugyo2.png',
    'g': 'Shogi_kinsho2.png',
    's': 'Shogi_ginsho2.png',
    'n': 'Shogi_keima2.png',
    'l': 'Shogi_kyosha2.png',
    'p': 'Shogi_fuhyo2.png',
}

piece_images = {}

active_piece = None
active_targets = []
active_moves = {}


def get_targets(piece):
    moves = piece.get_moves()
    targets = []
    global active_moves
    for move in moves:
        x, y = piece.x+move.dx, piece.y+move.dy
        active_moves[(x,y)] = move
        targets.append((x, y))
    return targets


def slide_piece(win, player, move):
    x1 = move.piece.x
    y1 = move.piece.y
    x2 = x1 + move.dx
    y2 = y1 + move.dy
    
    offset_x = 30
    offset_y = 70
    cell_width = 43
    cell_height = 43
    for i in range(20):
        x = (x1 + (i/20.0) * move.dx) * cell_width + offset_x
        y = (y1 + (i/20.0) * move.dy) * cell_height + offset_y
        symbol = str(move.piece)
        if move.piece.player == game.players[0]:
            symbol = symbol.lower()
        image = piece_images[symbol]
        win.blit(image, (x, y))
        display.flip()
        pygame.time.wait(10)
        
    player.do_move(move)
    

class BoardWidget(object):

    def __init__(self, board):
        self.board = board


    def draw(self, win):
        offset_x = 30
        offset_y = 70
        win.blit(board_image, (offset_x-20, offset_y-20))
        cell_width = 43
        cell_height = 43
        for i in range(9):
            for j in range(9):
                x1 = cell_width*j + offset_x
                y1 = cell_height*i + offset_y
                x2 = cell_width*(j+1) + offset_x - 1
                y2 = cell_height*(i+1) + offset_y - 1
                
                if self.board.cells[i][j] is not None:
                    symbol = str(self.board.cells[i][j])
                    if self.board.cells[i][j].player == game.players[0]:
                        symbol = symbol.lower()
                    image = piece_images[symbol]
                    win.blit(image, (x1+1,y1+1))
                
                if (j, i) in active_targets:
                    col = (255,0,0)
                    #draw.line(win, col, (x1,y1), (x2,y1), 1)
                    #draw.line(win, col, (x1,y2), (x2,y2), 1)
                    #draw.line(win, col, (x1,y1), (x1,y2), 1)
                    #draw.line(win, col, (x2,y1), (x2,y2), 1)
                    draw.circle(win, col, (x1+cell_width/2,y1+cell_height/2), 6, 0)
                    
                #score = ai.get_score(game, j, i)
                #win.blit(Font.render('%0.1f' % score, 1, (155, 155, 155), (0,0,0)), (x1, y1))
        
        try:
            piece = self.board.cells[self.active_y][self.active_x]
            if piece is not None:
                textx = 475
                if piece.player == game.players[0]:
                    texty = 125+25
                else:
                    texty = 380+25
                win.blit(Font.render(piece.name, 1, (255,255,0), (0,0,0)), (textx, texty))    
        except IndexError:
            pass


    def on_mouse(self, pos):
        x,y = pos
        self.active_x = (x - 31)/43
        self.active_y = (y - 71)/43


    def on_mouse_down(self, pos):
        global active_piece, active_targets
        try:
            piece = self.board.cells[self.active_y][self.active_x]
            if game.winner is None and piece is not None and piece.player == game.players[game.current_player]:
                active_piece = piece
                active_targets = get_targets(piece)
                self.last_x = self.active_x
                self.last_y = self.active_y
        except IndexError:
            active_piece = None

    def on_mouse_up(self, win, pos):
        global active_piece, active_targets, active_moves
        if active_piece is not None and (self.last_x,self.last_y) != (self.active_x,self.active_y):
            try:
                if self.board.cells[self.active_y][self.active_x] is not None:
                    gong_sound.set_volume(0.25 + random.random()/4.0)
                    gong_sound.play()
                move = active_moves[(self.active_x,self.active_y)]
                slide_piece(win, game.players[game.current_player], move)
            except (IndexError, KeyError):
                pass
        active_piece = None
        active_targets = []
        active_moves = {}


last_drawn_x, last_drawn_y = 0,0

def erasecusor(win):
    global last_drawn_x, last_drawn_y
    r = pygame.Rect(last_drawn_x, last_drawn_y, 38,38)
    draw.rect(win, (0,0,0), r, 0)

def drawcursor(win, pos):
    x,y = pos
    global last_drawn_x, last_drawn_y
    global active_piece
    
    if active_piece is not None:
        last_drawn_x,last_drawn_y = x-19,y-19
        symbol = str(active_piece)
        if active_piece.player == game.players[0]:
            symbol = symbol.lower()
        image = piece_images[symbol]
        win.blit(image, (last_drawn_x, last_drawn_y))
        


def main():
    init()

    win = display.set_mode((650, 500))
    display.set_caption("Shogi")

    global Font
    Font = font.Font(None, 26)

    global game
    game = Game()
    board_widget = BoardWidget(game.board)
    
    pygame.init()
    global board_image
    board_image = pygame.image.load(board_image_filename).convert()
    for name,filename in piece_image_filenames.iteritems():
        image = pygame.image.load(filename).convert()
        image = pygame.transform.scale(image, (40, 40))
        piece_images[name] = image
        
    while True:
        for e in event.get():
            if e.type == QUIT:
                return
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    return
                else:
                    global LastKey
                    LastKey = e.key
            if e.type == MOUSEBUTTONDOWN:
                board_widget.on_mouse_down(mouse.get_pos())
                event.set_grab(1)
            elif e.type == MOUSEBUTTONUP:
                board_widget.on_mouse_up(win, mouse.get_pos())
                event.set_grab(0)
            if e.type == VIDEORESIZE:
                win = display.set_mode(e.size, RESIZABLE)
        
        erasecusor(win)
        drawbackground(win)
        board_widget.on_mouse(mouse.get_pos())
        board_widget.draw(win)
        drawcursor(win, mouse.get_pos())

        display.flip()
        time.wait(25)
        computer_player(win)

if __name__ == '__main__':
    main()
    pygame.quit()
    print 'bye'
    