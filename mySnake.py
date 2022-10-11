import random, copy, pdb
from collections import deque
from blessed import Terminal
from threading import Timer

UP = 'UP'
DOWN = 'DOWN'
LEFT = 'LEFT'
RIGHT = 'RIGHT'

class Game:
    #游戏需要和世界交互，比如初始化一个世界。
    #游戏需要和Terminal交互，比如需要获取用户的键盘输入来进行游戏的控制。
    def __init__(self):
        self.score = 0
        self.quit = False
        self.term = Terminal()
        self.world = World(self, self.term)
        try:
            self.run()
        except Exception as e:
            with open('error.log', 'a') as f:
                f.write(str(e) + '\n')

    def run(self):
        self.world.re_draw()
        self.world.snake.move()
        with self.term.cbreak(), self.term.hidden_cursor():
            while self.quit == False:
                #这是一个阻塞方法
                key = self.term.inkey()
                if key.code == self.term.KEY_UP:
                    self.world.send_key(UP)
                elif key.code == self.term.KEY_DOWN:
                    self.world.send_key(DOWN)
                elif key.code == self.term.KEY_RIGHT:
                    self.world.send_key(RIGHT)
                elif key.code == self.term.KEY_LEFT:
                    self.world.send_key(LEFT)
                elif key == 'q':
                    break

    def over(self):
        self.quit == True
        print('Game Over!')

class World:
    #World需要和Game进行交互，通知蛇头碰到Border游戏结束。
    #World需要和Terminal进行交互，需要刷新控制台显示。
    #World需要和Grid进行交互，这样才能检查两个物体是否重叠，重叠后如何处理，如果是蛇头和苹果重叠那就吃掉苹果，如果和Snake或者Border重叠了就通知Game Over。
    WIDTH = 20
    HEIGHT = 15
    BORDER = '-'
    APPLE = 'x'
    SPACE = ' '

    def __init__(self, game, term):
        self.game = game
        self.term = term
        self.grid = Grid(self, World.WIDTH, World.HEIGHT)
        self.snake = Snake(self.grid, self)
        self.put_apple()

    def send_key(self, key):
        self.snake.turn_direction(key)
        
    def re_draw(self):
        self.clear()
        self.draw()

    def draw(self):
        for row in self.grid.rows:
            print(' '.join(row))
        print(f'Score = {self.game.score}')

    def clear(self):
        print(self.term.home + self.term.clear)

    def put_apple(self):
        empty_spaces = self.grid.list_empty_spaces()
        #pos is (row, col)
        apple_pos = random.choice(empty_spaces)
        self.grid.rows[apple_pos[0]][apple_pos[1]] = World.APPLE

    def overlap(self, head_char):
        #蛇头和墙重叠直接GameOver
        if head_char == World.BORDER:
            self.snake.dead = True
            self.game.over()
            return
        #如果和身体重叠需要判断是否为环，如果为环游戏继续，否则游戏结束。
        if head_char == Snake.BODY:
            #蛇身有一种情况是首位相连-->Circle，也就是头吃到了尾巴，这种情况不能算死。
            #这里需要注意的是如果和Border重叠就不能检测is_circle，否则数组的访问会越界。
            if self.snake.is_circle():
                return
            self.snake.dead = True
            self.game.over()
            return
        #蛇头和苹果重叠
        self.game.score += 1
        self.put_apple()
        self.snake.speed_up()
        self.snake.grow()

class Grid:

    #Grid需要和World交互，比如在数据变更后需要World重新绘制。
    def __init__(self, world, width, height):
        self.world = world
        self.width = width
        self.height = height
        self.rows = [[' ' for cell in range(self.width)] for row in range(self.height)]
        self.setBorder()

    def setBorder(self):
        # 竖线
        for i in range(self.height):
            self.rows[i][0] = World.BORDER
            self.rows[i][-1] = World.BORDER
        # 横线
        for i in range(self.width):
            self.rows[0][i] = World.BORDER
            self.rows[-1][i] = World.BORDER

    def set(self, cells):
        for cell in cells:
            self.rows[cell.row][cell.col] = cell.char
        self.world.re_draw()

    def set_space(self, cells):
        for cell in cells:
            self.rows[cell.row][cell.col] = ' '

    def list_empty_spaces(self):
        res = []
        for i, row in enumerate(self.rows):
            for j, cell in enumerate(row):
                if cell == ' ':
                    res.append((i, j))
        return res

    def get_char(self, cell):
        return self.rows[cell.row][cell.col]

class Cell:

    def __init__(self, row, col, char):
        self.row = row
        self.col = col
        self.char = char

class Snake:
    BODY = '*'
    HEAD = '#'
    INIT_SPEED = 0.4
    INIT_HEAD_POS = [10, 10]
    INIT_DIRECTION = RIGHT
    #Snake需要和Grid交互，比如Snake移动后Grid的数据需要修改。
    def __init__(self, grid, world):
        self.grid = grid
        self.world = world
        self.cells = deque([Cell(Snake.INIT_HEAD_POS[0], Snake.INIT_HEAD_POS[1], Snake.HEAD),\
                            Cell(Snake.INIT_HEAD_POS[0], Snake.INIT_HEAD_POS[1] - 1, Snake.BODY),\
                            Cell(Snake.INIT_HEAD_POS[0], Snake.INIT_HEAD_POS[1] - 2, Snake.BODY)])
        self.grid.set(self.cells)
        self.direction = Snake.INIT_DIRECTION
        self.next_direction = Snake.INIT_DIRECTION
        self.speed = Snake.INIT_SPEED
        self.dead = False

    def grow(self):
        self.cells.append(self.tail)

    def speed_up(self):
        self.speed = self.speed * 0.9

    def is_circle(self):
        head = self.cells[0]
        return self.tail.row == head.row and self.tail.col == head.col

    def turn_direction(self, direction):
        #如果不拆分为当前运动的方向direction和下一次移动或者说前进的方向next_direction会造成一个问题：
        #假设蛇只有一个方向属性，当前蛇头朝下，那么在下一次移动之前按左再按上就把蛇头运动方向朝自己了。
        #为了避免类似的情况所以设计了当前方向和下一次移动的方向，以此限制上述情况的发生。
        match self.direction:
            case 'DOWN':
                if direction in (LEFT, RIGHT):self.next_direction = direction
            case 'UP':
                if direction in (LEFT, RIGHT):self.next_direction = direction
            case 'LEFT':
                if direction in (UP, DOWN):self.next_direction = direction
            case 'RIGHT':
                if direction in (UP, DOWN):self.next_direction = direction

    def move(self):
        #保存一下移动前的cells，后面需要用来清除移动前的蛇。
        cells_before_move = copy.deepcopy(self.cells)
        #1.头变身体
        self.cells[0].char = Snake.BODY
        #2.弹出尾巴
        self.tail = self.cells.pop()
        #3.Push新的头进队列，appendleft
        match self.next_direction:
            case 'DOWN':
                self.cells.appendleft(Cell(self.cells[0].row + 1, self.cells[0].col, Snake.HEAD))
            case 'UP':
                self.cells.appendleft(Cell(self.cells[0].row - 1, self.cells[0].col, Snake.HEAD))
            case 'RIGHT':
                self.cells.appendleft(Cell(self.cells[0].row, self.cells[0].col + 1, Snake.HEAD))
            case 'LEFT':
                self.cells.appendleft(Cell(self.cells[0].row, self.cells[0].col - 1, Snake.HEAD))
        head = self.cells[0]
        head_char = self.grid.get_char(head)
        if head_char in (World.APPLE, World.BORDER, Snake.BODY):
            self.world.overlap(head_char)
        #4.更新Grid，如果移动后的蛇碰到身体或者墙就不能再往下执行gird.set，否则会出现蛇头把墙覆盖的效果。
        if not self.dead:
            #清除之前的身体和头
            self.grid.set_space(cells_before_move)
            self.grid.set(self.cells)
            self.direction = self.next_direction
            Timer(self.speed, self.move).start()

game = Game()
