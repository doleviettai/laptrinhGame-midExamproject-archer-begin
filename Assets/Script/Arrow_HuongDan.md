# Arrow - ban bang phim J

Khong co C#; chi co Script Graph, Prefab va cac component Unity co san.

## Player
GameObject: Player. Dung Script Machine co san, graph Player_flip.
Object Variables: ArrowPrefab (GameObject = Assets/Prefabs/Arrow.prefab);
ArrowSpawnPoint (GameObject = Player/ArrowSpawnPoint);
canShoot (Boolean = true); shootDelay (Float = 0.9).
ArrowSpawnPoint la GameObject rong con Player, Local Position (1.0625, -0.25, 0).

Flow: On Update -> If (Input Get Key Down, J) -> If (canShoot) ->
Set Object Variable canShoot = false -> Animator Set Trigger (isAttack) ->
Timer Start (shootDelay = 0.9) -> Completed -> Object Instantiate
(Original, Position, Rotation) -> Timer Start (0.2) ->
Completed -> Set Object Variable canShoot = true.
On Start -> Set Object Variable canShoot = true.

Data: Get Object Variable ArrowPrefab -> Instantiate Original.
Get Object Variable ArrowSpawnPoint -> Transform Get Position -> Instantiate Position.
Quaternion Get Identity -> Instantiate Rotation.
Get Object Variable shootDelay -> Timer Duration.
Get Object Variable canShoot -> If Condition.

Animator: isAttack la Trigger. Idle va Walking deu co transition vao Attack.
Attack -> Idle: Conditions rong, Has Exit Time bat, Exit Time = 1, Duration = 0.

## Arrow Prefab
GameObject: Arrow. Components: Sprite Renderer; Rigidbody 2D;
Box Collider 2D; Variables; Script Machine (graph ArrowFly).
Sprite: arrow_0 trong arrow.png. PPU 16; Point; Compression None.
Rigidbody 2D: Dynamic, Gravity Scale = 0, Freeze Position Y, Freeze Rotation Z.
Box Collider 2D: Is Trigger bat; Size (1.75, 0.1875). Tag PlayerArrow.
Sorting Layer Enemy, Order in Layer 5 (de hien tren Player/Enemy, duoi Foreground).
Object Variables: arrowSpeed (Float = 18); arrowLifetime (Float = 3).

Flow: On Start -> Rigidbody 2D Set Linear Velocity -> Object Destroy (Object, t).
Data: Get Object Variable arrowSpeed -> Vector2 Create X, Y = 0 ->
Set Linear Velocity Value. Target = Self.
Self (This) -> Destroy Object; Get Object Variable arrowLifetime -> Destroy t.
Destroy phai xoa ca GameObject Arrow, khong chi SpriteRenderer/ScriptMachine.

Chi co Prefab trong Project. Scene ban dau khong co doi tuong Arrow.
Moi lan J hop le sinh mot Arrow(Clone), bay ngang sang phai; tu huy sau 3 giay.
Mui ten chua gay sat thuong; se noi phan sat thuong khi lam Enemy.

## Kien thuc bo sung
Input Get Key Down (J), Vector2 Create va Self (This) neu chua hoc.
Timer, Instantiate, Quaternion Identity, Object Variables va Rigidbody2D
Set Linear Velocity la nhung node da nam trong danh sach bai hoc.
Set Trigger phai dung Animator parameter kieu Trigger.
Ban nay bay +X (sang phai); huong ban theo Flip X se la buoc rieng khi can.

## Kiem tra
1. Thoat Play, mo lai SampleScene neu Unity chua tai thay doi tu dia.
2. Chon Player -> Script Machine -> Edit Graph, tim Player Attack - J - Spawn Arrow.
3. Play, bam vao Game: chua bam J thi Hierarchy khong co Arrow(Clone).
4. Bam J: nhan vat keo cung; sau khoang 0.9 giay co mot Arrow(Clone) roi cung, bay sang phai.
5. Giu J khong tu dong ban lien tuc. Moi phat cach nhau it nhat khoang 1.1 giay.
6. Arrow tu huy sau 3 giay; Player van di chuyen va nhay Space.
7. Doi arrowSpeed trong Prefab de chinh toc do; shootDelay trong Player de chinh thoi diem roi cung.

Da kiem tra cau truc graph, cac port tu source Visual Scripting 1.9.12
va API Instantiate/Destroy tu XML cua Unity 6000.3.22f1 cai tren may.
Can kiem tra Play thuc te de xac nhan thoi diem va vi tri roi cung.
