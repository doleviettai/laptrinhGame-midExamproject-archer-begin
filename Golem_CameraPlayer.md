# Golem chỉ thức khi vào camera Player

Áp dụng cho cả GolemBlueCombat và GolemYellowCombat.

**Nguyên nhân cũ:** On Became Visible có thể bị camera Scene view kích hoạt khi Game camera còn ở xa.
**Cách mới:** dùng Camera.WorldToViewportPoint với GameObject Main Camera bên trong Player, giống SkeletonCombat.

## Biến Object

- MainCamera: GameObject = Player/Main Camera, đã gán trên cả hai Golem.
- isAwake: Boolean = False; On Start cũng đặt lại False.
- Máu giữ theo bản người dùng vừa lưu: Blue 9, Yellow 5.

## Nhóm 02 — Camera Player phát hiện

Data: MainCamera → Camera World To Viewport Point, Target.
This → Transform Get Position → World To Viewport Point, Position.
Kết quả Vector3 được tách X, Y, Z; kiểm tra X>0, X<1, Y>0, Y<1, Z>0 rồi ghép And.

Flow: On Update → If isAwake.
- True → hành vi đuổi/đánh hiện có.
- False → If điều kiện viewport. True → Set Object isAwake=True → hành vi hiện có.
- Nếu viewport False: Set Linear Velocity X=0 → Animator Set Bool isWalk=False.

Khung 02 dùng một This riêng. Các khung xử lý đánh, Hurt, trừ máu và Die giữ nguyên.

Sau lần đầu vào camera, isAwake giữ True và Golem tiếp tục đuổi, cùng cách Skeleton hoạt động.
Đây là điều kiện bắt đầu đuổi, không phải tự quên Player mỗi lần rời màn hình.

## Kiến thức bổ sung

Camera.WorldToViewportPoint, Vector3 Get X/Y/Z và And.
Chỉ dùng Unity API node và Visual Scripting, không có C#.

## Kiểm tra trong Unity

1. Trước Play, đặt Player xa Golem; vẫn có thể nhìn Golem trong Scene view.
2. Play: Golem ngoài camera Game phải đứng Idle, isAwake=False, vận tốc X=0.
3. Đưa Player đến để Golem vào camera Game: isAwake=True, Golem mới chạy đến và đánh.
4. Thoát Play rồi chạy lại: isAwake đặt lại False.
5. Arrow/Hurt/Die và máu Blue 9 / Yellow 5 giữ nguyên.
