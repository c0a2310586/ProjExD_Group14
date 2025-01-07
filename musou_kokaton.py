import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
reference = 200  # 場面変化の基準スコア
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


def show_instructions(screen):
    font = pg.font.Font("C:/Windows/Fonts/msgothic.ttc", 50) # 日本語フォントを指定
    instructions = [
        "操作説明:",
    "WASDキー: こうかとんを移動",
    "左Shiftキー: 高速化",
    "左クリック: ビーム発射",
    "右クリック: 弾幕",
    "リターンキー: 重力場 (100スコア消費)",
    "RShift: 無敵モード (50スコア消費)",
    "[l]キー: 防御壁 (50スコア消費)",
    "[e]キー: 敵機と爆弾の無効化 (20スコア消費)",
    ]

    screen.fill((0, 0, 0)) # 背景を黒に塗りつぶす
    for i, line in enumerate(instructions):
        text = font.render(line, True, (255, 255, 255)) # 白色でテキストを描画
        screen.blit(text, (50, 50 + i * 60)) # テキストを表示

    # 「Sを押して戻る」のメッセージ
    back_message = "Bキーを押して戻る"
    back_text = font.render(back_message, True, (255, 0, 0))  # 赤色で描画
    screen.blit(back_text, (50, 50 + len(instructions) * 60))  # 操作説明の下に表示

    pg.display.update()  # 画面更新
    while True:
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_b:
                return  # Sキーで操作説明を終了し、ゲーム開始画面に戻る

def check_game_clear(score: "Score", screen):
    if score.value > 1100:
        font = pg.font.Font(None, 80)
        text = font.render("ゲームクリア！", True, (255, 255, 0))
        rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(text, rect)
        pg.display.update()
        time.sleep(3)
        return True
    return False


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_w: (0, -1),
        pg.K_s: (0, +1),
        pg.K_a: (-1, 0),
        pg.K_d: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state="normal"  # 初期状態は通常
        self.hyper_life=0  # 発動時間の変数

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], lclick, senkai, screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)  # 無敵時の画像変換
            self.hyper_life -= 1
            if self.hyper_life < 0:
                self.state = "normal"  # 無敵状態終了

        if lclick is True:  # beamから向き判定の適用
        #     screen.blit(self.image, self.rect)
        # else:
        #     screen.blit(pg.transform.rotozoom(pg.transform.flip(img0, True, True), self.angle, 0.9), self.rect)
            if senkai <= 90:  #右半分
                self.birdimg = pg.transform.rotozoom(pg.transform.flip(pg.transform.rotozoom(pg.image.load(f"fig/3.png"), 0, 1), True, False), senkai, 1.1)
            else:  # 左半分
                self.birdimg = pg.transform.rotozoom(pg.transform.flip(pg.transform.rotozoom(pg.image.load(f"fig/3.png"), 0, 1), True, True), senkai, 1.1)
            screen.blit(self.birdimg, self.rect)
        else:
            screen.blit(self.image, self.rect)

        if key_lst[pg.K_LSHIFT]:
            self.speed = 20
        else:
            self.speed = 10


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    def __init__(self, emy: "Enemy", bird: Bird, speed: int , angle0: float=0):
        """
        爆弾Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        引数3 speed：爆弾の速度
        引数4 angle：爆弾の角度
        """
        super().__init__()
        self.state = "active"
        size = random.randint(30, 80)  # 爆弾のサイズ：30以上80以下の乱数
        img = pg.image.load(f"fig/bomb.png")
        img_width, img_height = img.get_size()  # 元の画像の縦横比を取得
        if img_width > img_height:
            # 幅を基準にリサイズ
            height = size
            width = int((img_width / img_height) * height)
        else:
            # 高さを基準にリサイズ
            width = size
            height = int((img_height / img_width) * width)

        self.image = pg.transform.scale(img, (width, height))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.angle = math.degrees(math.atan2(self.vy, self.vx))  # 角度を計算（上方向が0度になるように）
        self.image = pg.transform.rotozoom(self.image, self.angle, 1.0)  # 爆弾画像を回転
        self.rect = self.image.get_rect(center=(emy.rect.centerx, emy.rect.centery + emy.rect.height // 2))  # 回転後に中心を再設定

        angle0 += self.angle  # 追加されたangle0との合成
        rad_angle0 = math.radians(angle0)
        self.vx = math.cos(rad_angle0)
        self.vy = math.sin(rad_angle0)
        self.rect.centery = emy.rect.centery + emy.rect.height * self.vy
        self.rect.centerx = emy.rect.centerx + emy.rect.width * self.vx
        self.speed = speed

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0: float=0):
        """
        ビーム画像Surfaceを生成する
        取得したマウスカーソルの座標に向けて、こうかとんから飛んでいく
        引数 bird：ビームを放つこうかとん
        引数 angle：ビームの発射角度（Noneの場合、マウス方向）
        """
        super().__init__()
        self.vx, self.vy = bird.dire 
        mousex, mousey = pg.mouse.get_pos()
        angle = 90 + math.degrees(math.atan2(bird.rect.centerx - mousex, bird.rect.centery - mousey))  # atan2が三角関数より弧度法で算出, degreesで度数法に変換
        self.angle = angle
        rad_angle = math.radians(angle)
        self.vx = math.cos(rad_angle)
        self.vy = -math.sin(rad_angle)
        angle0 += self.angle  # 追加されたangle0との合成
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle0, 1.0)
        rad_angle0 = math.radians(angle0)
        self.vx = math.cos(rad_angle0)
        self.vy = -math.sin(rad_angle0)
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx
        self.speed = 10

    def update(self, bird: Bird, screen: pg.surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        
        if check_bound(self.rect) != (True, True):
            self.kill()

    def senkai(self):
        return self.angle


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


# class Boom(pg.sprite.Sprite):
#     """
#     爆発に関するクラス
#     """
#     def __init__(self, obj: "Bomb", screen: pg.Surface):
#         """
#         爆弾がこうかとんと衝突して爆発するエフェクトを生成する
#         引数1 obj：爆発するBombインスタンス
#         引数2 life：爆発時間
#         """
#         super().__init__()
#         img = pg.image.load(f"fig/boom.png")
#         self.image = pg.transform.scale(img, (obj.rect.width*2, obj.rect.height*2))  # 爆弾のサイズに合わせる
#         self.rect = self.image.get_rect(center=obj.rect.center)
#         screen.blit(self.image, self.rect)
    
#     def update(self):
#         """
#         爆発エフェクトを表現する
#         """
#         self.screen.blit(self.image, self.rect)


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class NeoBeam:
    def __init__(self, bird: Bird, num: int):
        self.bird = bird
        self.num = num

    def gen_beams(self) -> list[Beam]:
        step = 100 // (self.num - 1)
        angles = range(-50, 51, step)
        return [Beam(self.bird, angle) for angle in angles]
    

class BombProjectile:
    """
    敵が発射する爆弾に関するクラス
    """
    def __init__(self, emy: "Enemy", bird: "Bird", b_count: int, b_speed: int):
        """ 
        引数1 emy: Enemyクラスの引数
        引数2 bird: Birdクラスの引数
        引数3 b_count: 発射する爆弾の数
        引数4 b_speed: 爆弾の速度
        """
        self.emy = emy   # Enemyクラスの引数
        self.bird = bird   # Birdクラスの引数
        self.b_count = b_count
        self.b_speed = b_speed

    def gen_bombs(self) -> list[Bomb]:
        """
        指定された数の爆弾を生成し、リストとして返す
        戻り値: 複数のBombインスタンスを格納したリストlist[Bomb]
        """
        step = 100 // (self.b_count - 1)  # 爆弾間の角度差
        angles = range(-50, 51, step)  # 爆弾の角度範囲
        # 爆弾を生成し、リストに追加
        bombs = [Bomb(self.emy, self.bird, self.b_speed, angle) for angle in angles]
        return bombs
    

class Gravity(pg.sprite.Sprite):
    """
    重力場発動のクラス
    """
    def __init__(self, life = 400):
        """
        背景用surfaceを生成する
        引数life: 発動時間, 400に設定
        背景の透明度: 50
        """
        super().__init__()
        self.life = life  # 発動時間を設定, 以後update()にて減算
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (0, 0, 0), pg.Rect(0, 0, WIDTH, HEIGHT))  # 黒色を設定
        self.image.set_alpha(50)  # 透明度50
        self.rect = self.image.get_rect()


    def update(self, screen: pg.Surface):
        """
        lifeを呼び出し毎に減算
        screenへの反映
        """
        if self.life < 0:
            # print(self.life)
            self.kill()
        self.life -= 1  # lifeの減算
        screen.blit(self.image, self.rect)  # screenに反映


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class EMP:
    def __init__(self, enemies, bombs, screen):
        self.enemies = enemies
        self.bombs = bombs
        self.screen = screen
        self.active = False
        self.timer = 0

    def activate(self):
        self.active = True
        for enemy in self.enemies:
            enemy.interval = float('inf')
            enemy.image = pg.transform.laplacian(enemy.image)
        for bomb in self.bombs:
            bomb.speed //= 2
            bomb.state = "inactive"

    def deactivate(self):
        self.active = False
        for enemy in self.enemies:
            enemy.interval = random.randint(50, 300)
            # 元の画像に戻す処理が必要な場合はここで行う
        for bomb in self.bombs:
            bomb.speed *= 2

    def update(self):
        if self.active:
            self.timer += 1
            if self.timer % 5 == 0:
                # 画面全体に透明度のある黄色矩形を描画
                surface = pg.Surface(self.screen.get_size(), pg.SRCALPHA)
                surface.fill((255, 255, 0, 128))  # 黄色で、透明度128
                self.screen.blit(surface, (0, 0))
                # 他のオブジェクトを描画するコードの後に配置

                self.timer = 0  # タイマーをリセット

class Shield(pg.sprite.Sprite):
    """
    防御壁に関するクラス
    """
    def __init__(self, bird: Bird, life: int):
        """
        防御壁Surfaceを生成する
        引数1 bird：防御壁を出現させるこうかとん
        引数2 life：防御壁の有効時間
        """
        super().__init__()
        width, height = 20, bird.rect.height * 2
        width, height = 20, bird.rect.width * 2
        self.image = pg.Surface((width, height))
        self.image.fill((0, 0, 255))  # 青色
        self.rect = self.image.get_rect()
        # こうかとんの向きに基づいて防御壁を配置
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy
        self.life = life

    def update(self):
        """
        防御壁の有効時間を管理
        """
        self.life -= 1
        if self.life < 0:
            self.kill()


class Boss(pg.sprite.Sprite):
    """
    ボスに関するクラス
    """
    def __init__(self, health: int):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load("fig/boss.png"), 0, 1.2)
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        self.health = health  # ボスの耐久値
        self.health = health # ボスの耐久値
        self.speed = 2  # 移動速度
        self.direction = 1  # 移動方向 (左右)
        self.attack_interval = 30  # 攻撃間隔（フレーム数）※更に短くする
        self.timer = 0  # 攻撃タイマー

    def update(self, bombs: pg.sprite.Group, bird: Bird):
        """
        Bossの移動と攻撃処理
        """
        # 左右に移動
        self.rect.x += self.speed * self.direction
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.direction *= -1

        # 攻撃処理
        self.timer += 1
        if self.timer >= self.attack_interval:
            self.shoot(bombs, bird)
            self.timer = 0  # タイマーをリセット

    def shoot(self, bombs: pg.sprite.Group, bird: Bird):
        """
        Bossが多方向に高速爆弾を発射する
        """
        angles = [-30, -15, 0, 15, 30]  # 多方向に発射する角度
        for angle in angles:
            bombs.add(BossBomb(self.rect.center, bird, angle, speed=15))  # 更に速い速度


class BossBomb(pg.sprite.Sprite):
    """
    Boss専用の爆弾クラス（多方向攻撃）
    """
    def __init__(self, center: tuple, bird: Bird, angle: float, speed: float):
        super().__init__()
        self.state = "active"
        rad = 20  # 爆弾円の半径
        self.image = pg.Surface((2 * rad, 2 * rad), pg.SRCALPHA)
        pg.draw.circle(self.image, (255, 0, 0), (rad, rad), rad)
        self.rect = self.image.get_rect(center=center)

        # 方向ベクトルを計算（angle分だけずらす）
        base_angle = math.atan2(bird.rect.centery - center[1], bird.rect.centerx - center[0])
        adjusted_angle = base_angle + math.radians(angle)
        self.vx = math.cos(adjusted_angle) * speed
        self.vy = math.sin(adjusted_angle) * speed

    def update(self):
        self.rect.move_ip(self.vx, self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class StartScreen:
    """
    ゲーム開始画面を管理するクラス
    """
    def __init__(self, screen):
        self.screen = screen
        self.font = pg.font.Font("C:/Windows/Fonts/msgothic.ttc", 80)  # 日本語フォント
        self.text = self.font.render("Sキーを押してゲーム開始！", True, (255, 0, 0))
        self.rect = self.text.get_rect(center=(WIDTH//2, HEIGHT//2))

        # タイトル表示
        self.title_font = pg.font.Font("C:/Windows/Fonts/msgothic.ttc", 100)  # タイトルのフォント
        self.title_text = self.title_font.render("真！真！無双こうかとん", True, (255, 255, 0)) # タイ
        self.title_rect = self.title_text.get_rect(center=(WIDTH//2, HEIGHT//4))

        self.instructions = self.font.render("操作説明を見る: Iキー", True, (0, 255, 0))
        self.instructions_rect = self.instructions.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))

        self.exit_text = self.font.render("Xキーを押したら終了", True, (128, 0, 128))  # 紫文字
        self.exit_rect = self.exit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 200))

        self.bg_img = pg.image.load("fig/6.png")  # スタート画面の背景画像

    def display(self):
        """
        タイトル画面を表示する
        """
        self.screen.blit(self.bg_img, [0, 0])   # 背景画像を表示
        self.screen.blit(self.title_text, self.title_rect)   # タイトルを表示
        self.screen.blit(self.text, self.rect)  # 開始メッセージを表示
        self.screen.blit(self.instructions, self.instructions_rect)   # 操作説明メッセージを表示
        self.screen.blit(self.exit_text, self.exit_rect)   # 終了メッセージを表示
        pg.display.update()   # 画面を更新


class StageManager:
    """
    ステージ進行を管理するクラス
    """
    def __init__(self, bird: Bird, score: Score):
        self.stage = 1  # 現在のステージ
        self.bird = bird
        self.score = score
        self.enemy_kill_count = 0  # 倒した敵の数
        self.font = pg.font.Font(None, 50)
        self.neobeam_ready = False  # NeoBeamの使用可能状態
        self.neobeam_uses = 0  # NeoBeam使用可能数
        self.enemy_kill_for_neobeam = 0

    def reset_neobeam_uses(self):
        """NeoBeamの使用回数をリセット"""
        self.neobeam_ready = True
        self.enemy_kill_for_neobeam = 0  # カウントをリセット
        self.neobeam_uses = 3  # NeoBeamの回数をリセット

    def display_neobeam_status(self, screen: pg.Surface):
        """NeoBeamの状態を画面に表示"""
        stage_font = pg.font.Font("C:/Windows/Fonts/msgothic.ttc", 30)  # 日本語フォント
        if self.neobeam_ready:
            neo_beams = self.neobeam_uses
            neobeam_text = stage_font.render(f"NeoBeam: 使用可能(残り{neo_beams}回)", True, (0, 255, 0))  # 緑色で描画
        else:
            remaining = max(0, 3 - self.enemy_kill_for_neobeam)
            neobeam_text = stage_font.render(f"NeoBeam: {remaining}体撃破で使用可能", True, (255, 0, 0))  # 赤色
        # テキストの位置を設定（画面左上に表示）
        stage_rect = neobeam_text.get_rect(topleft=(50, 20))
        screen.blit(neobeam_text, stage_rect)  # テキストを描画

    def check_stage_clear(self, screen, emys):
        """ステージ 1 のクリア条件を満たしたか確認"""
        if self.stage == 1 and self.enemy_kill_count >= 15:
            self.display_stage_clear(screen)
            emys.empty()  # ステージ1の敵をすべて消去
            self.stage += 1
            time.sleep(2) 
            return True
        return False
        
    def display_stage_clear(self, screen):
        """ステージクリアメッセージを表示"""
        font = pg.font.Font("C:/Windows/Fonts/msgothic.ttc", 80)  # 日本語フォント
        text = font.render(f"ステージ {self.stage} クリア！", True, (0, 255, 0))
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, rect)
        pg.display.update()

    def check_game_clear(self, screen, b_health):
        """ゲームクリア条件 (ボスを倒したか) を確認"""
        if self.stage == 2 and b_health == 0:  # ボスが倒されたら
            self.display_game_clear(screen)
            time.sleep(3) # ゲームクリア後に静止
            return True
        return False
        
    def display_game_clear(self, screen):
        """ゲームクリアメッセージを表示"""
        black_overlay = pg.Surface((WIDTH, HEIGHT))
        black_overlay.set_alpha(128)  # 半透明設定
        black_overlay.fill((0, 0, 0))  # 黒色
        screen.blit(black_overlay, (0, 0))  # 背景を描画

        font = pg.font.Font("C:/Windows/Fonts/msgothic.ttc", 80)  # 日本語フォント
        text = font.render("ゲームクリア！", True, (255, 255, 0))
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

        # 両端に喜んでいるこうかとん画像を配置
        img_left = pg.image.load("fig/6.png")
        img_right = pg.transform.flip(img_left, True, False)
        left_rect = img_left.get_rect(midright=(rect.left - 20, HEIGHT // 2))
        right_rect = img_right.get_rect(midleft=(rect.right + 20, HEIGHT // 2))

        screen.blit(text, rect)
        screen.blit(img_left, left_rect)
        screen.blit(img_right, right_rect)
        pg.display.update()

    def gameover(self, screen: pg.Surface):
        """
        ゲームオーバー画面を表示し、赤背景とテキストを描画する。
        """
        # 半透明の赤背景
        red_overlay = pg.Surface((WIDTH, HEIGHT))
        red_overlay.set_alpha(128)  # 半透明設定
        red_overlay.fill((255, 0, 0))  # 赤色
        screen.blit(red_overlay, (0, 0))  # 背景描画

        # テキスト表示
        font = pg.font.Font("C:/Windows/Fonts/msgothic.ttc", 80)  # 日本語フォント
        text = font.render("ゲームオーバー！", True, (255, 255, 255)) # 白文字
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, rect)

        # 泣いているこうかとん画像を表示
        img = pg.image.load("fig/8.png")  # 泣いているこうかとん
        img_rect = img.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))
        screen.blit(img, img_rect)
        # Bキーの説明
        sub_text = font.render("Bキーを押してタイトルへ", True, (255, 255, 255))
        sub_rect = sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))  # 文字間隔を調整
        screen.blit(sub_text, sub_rect)

        pg.display.update()

        while True:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN and event.key == pg.K_b:  # Bキーでタイトル画面に戻る
                    screen.fill((0, 0, 0))  # 画面をクリア
                    return

    def display_stage(self, screen):
        """右上にステージ進行状況を表示"""
        stage_font = pg.font.Font("C:/Windows/Fonts/msgothic.ttc", 30)
        # ステージ数の表示 (右下)
        stage_text = stage_font.render(f"ステージ: {self.stage}", True, (255, 0, 0))
        stage_rect = stage_text.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
        screen.blit(stage_text, stage_rect)

        # 敵の残数表示 (右上)
        if self.stage == 1:
            # 敵機の画像を読み込む
            enemy_image = pg.image.load("fig/alien1.png")
            enemy_image = pg.transform.scale(enemy_image, (20, 20))

            # テキストのレンダリング
            remaining_text = stage_font.render(f"残り:", True, (255, 255, 255))
            remaining_rect = remaining_text.get_rect(topright=(WIDTH - 100, 20))

            # 画像の表示位置
            enemy_rect = enemy_image.get_rect(topright=(remaining_rect.left - 10, 20))  # テキストの左

            # 画像とテキストの描画
            screen.blit(enemy_image, enemy_rect)
            screen.blit(remaining_text, remaining_rect)

            # 数字の描画
            number_text = stage_font.render(f"{15 - self.enemy_kill_count}", True, (255, 255, 255))
            number_rect = number_text.get_rect(topleft=(remaining_rect.right, 20))
            screen.blit(number_text, number_rect)

        else: # ステージ2
            # ボスの画像を読み込む
            boss_image = pg.image.load("fig/boss.png")
            boss_image = pg.transform.scale(boss_image, (30, 30))
            boss_text = stage_font.render("ボス", True, (255, 255, 255))
            boss_rect = boss_text.get_rect(topright=(WIDTH - 100, 20))
            screen.blit(boss_text, boss_rect)
            screen.blit(boss_image, boss_rect.topright)


def wait_for_start(screen):
    start_screen = StartScreen(screen)
    while True:
        start_screen.display()  # タイトル画面を表示
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s:  # Sキーでゲーム開始
                    return True
                if event.key == pg.K_i:  # Iキーで操作説明画面に切り替え
                    screen.fill((0, 0, 0))  # 画面を黒で塗りつぶす
                    show_instructions(screen)  # 操作説明を表示
                    screen.fill((0, 0, 0))  # 操作説明後に画面を再度黒で塗りつぶし
                    start_screen.display()  # タイトル画面を再表示
                if event.key == pg.K_x:  # Xキーでゲーム終了
                    pg.quit()
                    sys.exit()


def mouse_setting():
    """
    マウスカーソルを可視または不可視にする関数
    """
    pg.mouse.set_visible(True)
    print(pg.mouse.get_cursor())
    # pg.cursor.compile(strings, black='X', white='.', xor='o')
    # pg.mouse.set_cursor()


def main():
    while True:
        pg.display.set_caption("真！こうかとん無双")
    
        mouse_setting()  # カーソルの設定（可視不可視など）の関数

        screen = pg.display.set_mode((WIDTH, HEIGHT))
        bg_img = pg.image.load(f"fig/pg_bg.jpg")
        score = Score()
        if not wait_for_start(screen):  # ユーザーがゲームを開始しない場合終了
            return

        bird = Bird(3, (900, 400))
        bombs = pg.sprite.Group()
        beams = pg.sprite.Group()
        exps = pg.sprite.Group()
        # booms = pg.sprite.Group()
        emys = pg.sprite.Group()
        shield = pg.sprite.Group()
        gra = pg.sprite.Group()
        emp = EMP(emys, bombs, screen)
        bosses = pg.sprite.Group()
        boss_count = 0 # Boss数
        stage_manager = StageManager(bird, score)
        tmr = 0
        clock = pg.time.Clock()
        mouse_click = False
        senkai = 0

        while True:
            key_lst = pg.key.get_pressed()
            mouse_lst = pg.mouse.get_pressed()  # mouseの押下されたボタンのリスト
            if mouse_lst[0] == True:  # 左クリックがあれば条件式に入る
                bird.change_img(3, screen)  # こうかとんエフェクト
                if not mouse_click:
                    a = Beam(bird)
                    beams.add(a)
                    senkai = a.senkai()
                mouse_click = True

            elif mouse_lst[2] and stage_manager.neobeam_uses > 0:  # 右クリックでNeoBeam発射
                bird.change_img(3, screen)  # こうかとんエフェクト
                if not mouse_click:
                    neo_beam = NeoBeam(bird, 5)  # NeoBeamを生成（5方向）
                    beams.add(*neo_beam.gen_beams())  # 複数ビームを追加
                    stage_manager.enemy_kill_for_neobeam == 0  # 使用後に0
                    stage_manager.neobeam_uses -= 1  # 使用可能回数を減少
                    if stage_manager.neobeam_uses == 0:
                        stage_manager.neobeam_ready = False
                mouse_click = True
            else:
                mouse_click = False

            for event in pg.event.get():  # イベントリストを取得
                if event.type == pg.QUIT:
                    return 0
                
                if score.value >= 50 and (event.type == pg.KEYDOWN and event.key == pg.K_l):
                    shield.add(Shield(bird, life=400))
                    score.value -= 50  # スコア消費
                if score.value >= 100 and (event.type == pg.KEYDOWN and event.key == pg.K_RETURN):  # score100以上で
                    score.value -= 100  # scoreのうち100を消費
                    gra.add(Gravity())
                if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.value > 100:
                    bird.state = "hyper"
                    bird.hyper_life = 50
                    score.value -= 50  # スコア消費
                if score.value >= 20 and key_lst[pg.K_e] and not emp.active:
                    if score.value >= 20:
                        score.value -= 20
                    emp.activate()
                elif emp.active and key_lst[pg.K_e]:
                    emp.deactivate()

            screen.blit(bg_img, [0, 0])

            if stage_manager.stage == 1 and tmr % 200 == 0:
                emys.add(Enemy())

            for emy in emys:
                if emy.state == "stop" and tmr%emy.interval == 0:
                    # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                    if score.value < 50 or boss_count == 1:
                        bombs.add(Bomb(emy, bird, 6))
                    elif score.value < 100:
                        bomb_pro = BombProjectile(emy, bird, 3, 8)
                        bombs.add(*bomb_pro.gen_bombs())
                    else:
                        bomb_pro = BombProjectile(emy, bird, 5, 10)
                        bombs.add(*bomb_pro.gen_bombs())
                        
            # ボスの生成: ステージ 2
            if stage_manager.stage == 2:
                if boss_count == 0:
                    bosses.add(Boss(health=30))
                    boss_count = 1  # Bossが生成されたことを記録

                if tmr % 150 == 0 and len(emys) < 3:  # 敵を定期的に生成し、敵の数を3体まで制限する
                    emys.add(Enemy())
                    for emy in emys:
                        if emy.state == "stop" and tmr % emy.interval == 0:
                            bombs.add(Bomb(emy, bird, 6))

            for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト
                exps.add(Explosion(emy, 100))  # 爆発エフェクト
                score.value += 10  # 10点アップ
                bird.change_img(9, screen)  # こうかとん歌うエフェクト
                stage_manager.enemy_kill_count += 1
                stage_manager.enemy_kill_for_neobeam += 1  # NeoBeam用のカウントを増やす
                if stage_manager.enemy_kill_for_neobeam >= 3:
                    stage_manager.reset_neobeam_uses()

            for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
                if bomb.state == "active":
                    exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                    bird.change_img(6, screen)  # こうかとん喜びエフェクト
                    score.value += 1  # 1点アップ

            for bomb in pg.sprite.groupcollide(bombs, shield, True, True).keys():  # 防御壁と衝突した爆弾リスト
                if bomb.state == "active":
                    exps.add(Explosion(bomb, 50))  # 爆発エフェクト

            for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
                if bomb.state == "active":
                    if bird.state == "hyper":  # state="hyper"なら
                        exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                        score.value += 1  # 1点アップ
                    else:  # state="hyper"ではないなら
                        stage_manager.gameover(screen)

                        # 初期化処理を追加
                        score = Score()  # スコアをリセット
                        stage_manager = StageManager(bird, score)  # ステージ情報をリセット
                        tmr = 0  # タイマーをリセット
                        emys.empty()  # 敵キャラクターを全て削除
                        bombs.empty()  # 爆弾を全て削除
                        bosses.empty()  #　ボスを削除
                        exps.empty()
                        boss_count = 0
                        wait_for_start(screen) # タイトル画面に戻る
                        break # ゲームループから抜ける
                        
            for emy in pg.sprite.groupcollide(emys, gra, True, False).keys():  # 重力と衝突した敵機リスト
                exps.add(Explosion(emy, 100))  # 敵機の爆発エフェクト
            
            for bomb in pg.sprite.groupcollide(bombs, gra, True, False).keys():  # 重力と衝突した爆弾リスト
                exps.add(Explosion(bomb, 50))  # 爆弾の爆発エフェクト

            # Bossとビームの衝突判定
            for boss in pg.sprite.groupcollide(bosses, beams, False, True).keys():
                boss.health -= 1
                if boss.health <= 0:
                    exps.add(Explosion(boss, 200))

            # ステージクリア処理
            if stage_manager.check_stage_clear(screen, emys):
                continue # ステージ遷移
            # ゲームクリア処理
            for boss in bosses:
                b_health = boss.health
                if stage_manager.check_game_clear(screen, b_health):
                    time.sleep(2)
                    return
            # ゲームオーバー処理
            for bomb in pg.sprite.spritecollide(bird, bombs, True):
                if bird.state != "hyper":
                    stage_manager.gameover(screen)
                    break # タイトル画面に戻る

            bird.update(key_lst, mouse_click, senkai, screen)
            beams.update(bird, screen)
            beams.draw(screen)
            emys.update()
            emys.draw(screen)
            bombs.update()
            bombs.draw(screen)
            exps.update()
            exps.draw(screen)
            # booms.update()
            # booms.draw(screen)
            gra.update(screen)
            score.update(screen)
            bosses.update(bombs, bird)
            bosses.draw(screen)
            shield.update()
            shield.draw(screen)
            stage_manager.display_stage(screen)  # ステージ番号を右下に表示
            stage_manager.display_neobeam_status(screen)  # NeoBeamの状態を表示
            pg.display.update()
            tmr += 1
            clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
