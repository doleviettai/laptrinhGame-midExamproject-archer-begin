# Golem Yellow và Golem Blue

## Máu và sát thương

| Đối tượng | Máu khởi tạo | Sát thương mỗi đòn trúng |
|---|---:|---:|
| Player | 15 | Mỗi Arrow trúng gây 1 sát thương |
| Golem Blue — quái đặc biệt | 9 | 1 |
| Golem Yellow — quái thường | 5 | 1 |

Blue được đặt `health = 9` ở Object Variables trên scene và Integer Literal trong On Start của GolemBlueCombat.
Yellow dùng graph riêng GolemYellowCombat; On Start đặt health = 5.
Mỗi con giữ máu riêng; không chia sẻ biến App/Scene để lưu máu quái.

## Mở trong Unity

- Chọn Enemy → Golem_yellow → Script Machine → Edit Graph để xem GolemYellowCombat.
- Graph có 12 khung màu giống Golem Blue, mỗi khung có Comment giải thích.
- Animator dùng Golem_yellow.controller; toàn bộ Motion là clip màu vàng Golem_yl_*.

## Component của Golem Yellow

- Rigidbody 2D: Dynamic, Gravity Scale 3, Freeze Rotation Z.
- Box Collider 2D: Is Trigger tắt; Size (1.5632668, 1.4789243), Offset (-0.07003021, -0.9337318), khớp cùng loại sprite Golem Blue.
- Variables: health (Integer 5), Player (GameObject Player), moveSpeed (Float 2), isAwake (Boolean false), attackRange (Float 2), isAttacking (Boolean false), attackDelay (Float 0.4), attackRecovery (Float 0.8), isHurt (Boolean false).
- Script Machine: GolemYellowCombat. Tag Enemy.

## Luồng hành vi và nhận sát thương

1. On Start → health = 5, isAttacking = false, isHurt = false, isAwake = false.
2. Kiểm tra WorldToViewportPoint bằng Object MainCamera → chỉ khi vào camera Game của Player mới đặt isAwake = true, giống Skeleton.
3. On Update → nếu đã thức và không Hurt: ngoài tầm thì chọn hướng, Set Linear Velocity X, Flip X và isWalk=true.
4. Đủ gần: dừng X, isWalk=false, kiểm tra isAttacking để chỉ bắt đầu một đòn.
5. isAttacking=true → Animator Trigger doAttack → Timer attackDelay=0.4.
6. Timer Completed → kiểm tra lại tầm ngang → nếu trúng gửi Custom Event PlayerTakeDamage tới Player.
7. Trúng hay hụt đều qua Timer attackRecovery=0.8 → isAttacking=false.
8. On Trigger Enter 2D → collider → Get Game Object → Compare Tag PlayerArrow → If health > 0.
9. Destroy Arrow ngay → Subtract Integer 1 → Set Object health → kiểm tra Value mới > 0.
10. Còn máu: isHurt=true → Trigger gotHit → Timer 0.36 → isHurt=false; On Update dừng X và isWalk trong lúc Hurt.
11. Hết máu: Trigger doDie → velocity=(0,0) → gravityScale=0 → BoxCollider2D disabled → Destroy This sau 0.6 giây → ScriptMachine disabled.

Animation Die màu vàng dài khoảng 0.517 giây, nên thời gian hủy 0.6 giây cho clip phát xong.
Arrow giữ cách bắn sang phải như trước.

## Animator

Parameter: isWalk là Bool; doAttack, gotHit, doDie là Trigger.

| Chuyển state | Điều kiện |
|---|---|
| Golem_yl_idel → Golem_yl_walking | isWalk=true |
| Golem_yl_walking → Golem_yl_idel | isWalk=false |
| Any State → Golem_yl_attack | doAttack |
| Any State → Golem_yl_eat_hit | gotHit |
| Any State → Golem_yl_die | doDie |
| Attack/Hurt → Idle | Has Exit Time, Exit Time=1, Duration=0 |

Giữ nguyên tên clip/state có sẵn, kể cả tên `Golem_yl_idel`.
Attack/Hurt/Die không lặp; Idle và Walking lặp.

## Kiến thức bổ sung

Các phần đã học thêm cùng Golem Blue: Mathf Abs, đọc Transform.position và Vector3.x,
Set Linear Velocity X, Custom Event/Trigger Custom Event, và This.
Không tạo C#; game dùng component có sẵn và Script Graph.

## Kiểm tra

1. Thoát Play, tải lại SampleScene nếu Unity hỏi Reload.
2. Trong Play, chọn từng con và xem Object health: Blue bắt đầu 9, Yellow bắt đầu 5.
3. Tiến tới Yellow trên cùng mặt đất: Walking, quay mặt, đuổi; đến gần thì đánh và làm Player mất 1 máu mỗi đòn trúng.
4. Bắn Yellow: health 5 → 4 → 3 → 2 → 1 → 0. Arrow trúng biến mất; còn máu phát Hurt; hết máu phát Die và biến mất.
5. Bắn Blue cần 9 phát trúng để hết 9 máu.
6. Thoát Play, chạy lại: máu khởi tạo không bị giữ từ lượt trước.

Các Golem đuổi ngang, không có hệ thống tìm đường hoặc tự nhảy qua hố. Phát hiện dùng camera Game của Player; Scene camera không kích hoạt đuổi sớm.


Cập nhật phát hiện camera: xem [Golem_CameraPlayer.md](Golem_CameraPlayer.md).
