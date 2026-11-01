# Phân công và ôn vấn đáp Archer Survival — nhóm 2 người

Đây là đề xuất chia phần phụ trách, kiểm tra và trình bày. Hai bạn điền tên thật và điều chỉnh theo phần công việc thực tế của từng người.

## 1. Cách chia cân đối

| Thành viên | Phần phụ trách chính | Nội dung cần giải thích và demo |
|---|---|---|
| **Thành viên 1 — bạn** | **Player, Arrow, máu Player và UI người chơi** | Di chuyển, lật ảnh, nhảy; Animator Player; J bắn cung theo hướng nhìn; thanh máu đỏ; Hurt/Death; Game Over, Chơi lại và hướng dẫn K |
| **Thành viên 2** | **Map, enemy và tiến trình màn chơi** | Tilemap/Tile Palette/trang trí; camera; Skeleton, Golem Blue, Golem Yellow; phát hiện trong camera, đuổi, đánh, nhận Arrow; vùng đích, chiến thắng, Level2; lớp va chạm |

Phần Player/UI có nhiều thao tác nhập liệu và liên kết component. Phần enemy/map có nhiều thiết lập scene và hành vi, nhưng Golem Blue/Yellow dùng cấu trúc tương tự nên có thể giải thích theo một mẫu chung.

## 2. Thành viên 1: Player, Arrow, máu và UI

### Các chức năng cần nắm

1. **Di chuyển:** đọc Horizontal, nhân tốc độ và đặt Rigidbody2D Linear Velocity. Khi chỉnh vận tốc X, giữ vận tốc Y để không làm mất chuyển động rơi/nhảy.
2. **Quay mặt:** khi đi phải đặt Flip X = False và facingDirection = 1; khi đi trái đặt Flip X = True và facingDirection = -1. Thả phím vẫn giữ hướng cuối.
3. **Nhảy:** Space chỉ cho nhảy khi điều kiện chạm đất đạt; vận tốc Y nhận jumpSpeed. Asset Player không có clip nhảy nên không giới thiệu một animation Jump chưa có.
4. **Animator Player:** nêu được vai trò Idle, Walking, Attack, eat_hit, Death và các parameter đang dùng.
5. **Bắn cung:** J → kiểm tra canShoot → khóa bắn → Attack → Timer shootDelay → chỉnh điểm bắn → Instantiate → gán hướng cho Arrow(Clone) → hồi quyền bắn.
6. **Hướng Arrow:** arrowSpeed × direction tạo vận tốc X; direction âm thì Flip X của Arrow bật. ArrowSpawnPoint có Local X = facingDirection × 1.0625, Y = -0.25.
7. **Máu Player:** PlayerTakeDamage → kiểm tra còn sống → trừ 1 → Hurt hoặc Death. Máu tối đa hiện là **20**.
8. **Thanh đỏ:** mỗi Update lấy PlayerHealth / maxHealth bằng Divide số thực, gán vào Image Fill Amount. 19/20 = 0.95.
9. **Game Over:** PlayerHealth gửi PlayerDied sau chuỗi chết → GameUIManager hiện bảng, tạm dừng; nút Chơi lại khôi phục Time Scale rồi tải lại scene hiện tại.
10. **Hướng dẫn:** K bật/tắt bảng khi chưa chết và chưa thắng; mở thì tạm dừng, đóng thì chơi tiếp. Có cả nút Đóng.

### Các graph và đối tượng phải mở được ngay

| GameObject / prefab | Graph / component |
|---|---|
| Player | `Player_flip` trong Script Machine điều khiển |
| Arrow.prefab | `ArrowFly`, Variables, Rigidbody2D, collider Trigger |
| Player | `PlayerHealth` trong Script Machine xử lý máu |
| Canvas/Info/HealthBar/Fill | Image Type Filled, Horizontal, Origin Left |
| GameUIManager | Các khung khởi tạo, phím K, nút Đóng, PlayerDied và Chơi lại |

### Câu giới thiệu phần phụ trách

> Em phụ trách Player, cơ chế bắn cung và giao diện người chơi. Em dùng Visual Scripting để đọc phím, điều khiển Rigidbody2D, truyền hướng vào mũi tên vừa tạo, xử lý máu và cập nhật UI. Khi Player chết, graph gửi sự kiện cho GameUIManager hiện Game Over; các nút được bắt bằng On Button Click.

### Câu hỏi vấn đáp nên luyện

| Giảng viên hỏi | Ý chính cần trả lời |
|---|---|
| Vì sao Flip X Player rồi mũi tên vẫn bay phải trong bản cũ? | Flip X chỉ lật SpriteRenderer; bản cũ đặt vận tốc X mũi tên luôn dương. Cần direction = 1/-1 để tính vận tốc. |
| Vì sao direction phải ghi lên Result của Instantiate? | Result là Arrow(Clone) vừa sinh. Ghi lên prefab hoặc This của Player không đặt đúng biến cho từng mũi tên. |
| Vì sao phải đổi cả ArrowSpawnPoint? | Lật sprite không tự chuyển vị trí GameObject con. Cần Local X mang dấu của hướng nhìn. |
| canShoot dùng làm gì? | Chặn việc tạo thêm đòn khi lần bắn hiện tại chưa hoàn tất thời gian chờ/hồi. |
| Started và Completed của Timer khác nhau thế nào? | Started chạy khi bắt đầu đếm; Completed chạy khi đếm đủ. Instantiate phải ở sau Completed của thời gian kéo cung. |
| Vì sao thanh máu dùng phép chia số thực? | Cần tỷ lệ 0–1 và giữ phần lẻ; ví dụ 19/20 phải là 0.95. |
| Tại sao máu nhập 20 trong Inspector nhưng trước đây Play lại thành 15? | On Start còn ghi đè số 15. Hiện khởi tạo PlayerHealth từ maxHealth = 20. |
| Chơi lại sao không luôn tải SampleScene? | Cần GetActiveScene rồi lấy name để chết ở Level2 thì tải lại Level2. |
| Vì sao đặt Time Scale về 1 trước Load Scene? | Time Scale không tự bảo đảm trở về bình thường khi đổi scene; nếu giữ 0 thì màn mới vẫn tạm dừng. |

### Tài liệu ôn

- [Player_ThanhMau.md](Player_ThanhMau.md).
- [UI_GameOver_HuongDan.md](UI_GameOver_HuongDan.md).
- Graph Player_flip và ArrowFly bản hiện tại: dùng đúng dây bạn đã nối theo các bước sửa hướng bắn.

## 3. Thành viên 2: map, enemy và chuyển màn

### Các chức năng cần nắm

1. **Import và cắt sprite:** giải thích PPU 16, Filter Point, Compression None, chia sheet theo ô và tạo clip Animator đúng số frame đã dùng.
2. **Map:** Grid tổ chức Tilemap; Ground có Tilemap Collider 2D, Composite Collider 2D và Rigidbody2D Static. Decor/trang trí phục vụ hình ảnh, không thêm va chạm lên cây nền.
3. **Camera:** Main Camera là con Player nên đi theo Player; điều kiện đánh thức enemy dùng chính Game camera.
4. **Phát hiện enemy:** WorldToViewportPoint kiểm tra vị trí nằm trong viewport, rồi đặt isAwake = True. Sau khi thức, enemy tiếp tục đuổi dù ra ngoài màn hình.
5. **Đuổi:** đọc vị trí Player và enemy, tính hướng/khoảng cách, đặt vận tốc X và Flip X; bật isWalk khi di chuyển.
6. **Đánh:** trong tầm và chưa đánh → đặt isAttacking → Attack → chờ attackDelay → kiểm tra lại tầm → gửi PlayerTakeDamage → chờ attackRecovery → mở lại quyền đánh.
7. **Nhận Arrow:** On Trigger Enter 2D → Compare Tag PlayerArrow → hủy Arrow → trừ 1 máu → Hurt hoặc Die.
8. **Máu từng loại:** Skeleton **3**, Golem Yellow **5**, Golem Blue **9**. Các biến health là Object, mỗi đối tượng có máu riêng.
9. **Kết thúc màn:** FinishPoint nhận Player → gửi LevelCompleted → kiểm tra chưa chết/chưa thắng → hiện VictoryCanvas, tắt điều khiển, tạm dừng.
10. **Qua màn:** nút đọc Object Variable NextScene và LoadScene. SampleScene chuyển Level2; kết thúc Level2 có thể về SampleScene.
11. **Va chạm thân:** PlayerBody và EnemyBody không chặn nhau; vẫn tương tác Ground. Arrow ở Default vẫn tương tác EnemyBody. Sát thương cận chiến được graph kiểm tra theo tầm đánh.

### Các graph và đối tượng phải mở được ngay

| GameObject | Graph / thiết lập |
|---|---|
| Grid/Ground | Tilemap, TilemapCollider2D, CompositeCollider2D |
| Backdrop/EnvironmentDecor | SpriteRenderer và thứ tự vẽ cây |
| Enemy/Skeleton | `SkeletonCombat` và Animator |
| Enemy/Golem_blue | `GolemBlueCombat` và Animator |
| Enemy/Golem_yellow | `GolemYellowCombat` và Animator |
| FinishPoint | `FinishPoint`, BoxCollider2D có Is Trigger |
| GameUIManager | Khung LevelCompleted, hasWon và nút Qua màn mới |
| Project Settings | Layers và Physics 2D Layer Collision Matrix |
| Build Profiles | Scene List chứa SampleScene, Level2 |

### Câu giới thiệu phần phụ trách

> Em phụ trách map, hành vi enemy và tiến trình màn chơi. Map dùng Grid/Tilemap và tách phần có collider với phần trang trí. Enemy được đánh thức khi vào Game camera, sau đó đuổi, kiểm tra tầm đánh và nhận sát thương từ Arrow. Em cũng phụ trách vùng đích gửi sự kiện chiến thắng, chuyển scene và cấu hình các lớp va chạm thân nhân vật.

### Câu hỏi vấn đáp nên luyện

| Giảng viên hỏi | Ý chính cần trả lời |
|---|---|
| Vì sao không chỉ dùng On Became Visible để đánh thức enemy? | Camera Scene cũng có thể làm Renderer được xem là visible. Project cần Game camera nên dùng WorldToViewportPoint. |
| Enemy ra khỏi camera có ngủ lại không? | Hiện không: isAwake giữ True sau lần đầu phát hiện. |
| Enemy có thể đánh hụt không? | Có. Sau attackDelay phải kiểm tra lại tầm; Player ra khỏi tầm thì không gửi sát thương. |
| Vì sao cần isAttacking và isHurt? | isAttacking tránh bắt đầu đòn mỗi frame; isHurt ngăn luồng đi/đánh ghi đè phản ứng bị trúng đòn. |
| Vì sao mỗi con có health riêng? | health là Object Variable trên từng GameObject; không dùng một biến Scene/App chung cho mọi enemy. |
| Skeleton và Golem khác nhau gì? | Dùng cùng mô hình đuổi–đánh–Hurt–Die, nhưng graph/Animator và thông số riêng; ví dụ 3/5/9 máu. Không khẳng định mọi kiểm tra tầm giống hệt nhau. |
| TilemapCollider và CompositeCollider làm gì? | TilemapCollider tạo hình va chạm từ tile; Composite ghép các hình, giảm các đường biên nội bộ. |
| Layer và Sorting Layer khác nhau thế nào? | Layer dùng cho lọc/va chạm; Sorting Layer quyết định thứ tự vẽ SpriteRenderer/TilemapRenderer. |
| Vì sao ở MidTree_15 có cảm giác bị chắn? | Đã tái hiện va chạm Player–Golem Blue gần cây. Cây không có collider; tách physics Layer để thân nhân vật không cản nhau. |
| Làm sao Arrow chạm đích không làm thắng? | FinishPoint dùng Compare Tag Player trước khi gửi LevelCompleted. |
| hasWon có tác dụng gì? | Ngăn xử lý thắng nhiều lần và chặn mở hướng dẫn sau khi thắng. |
| Làm sao cùng graph chuyển được các scene khác nhau? | Mỗi scene gán Object Variable NextScene khác nhau cho GameUIManager. |

### Tài liệu ôn

- [Skeleton_LuongHoatDong.md](Skeleton_LuongHoatDong.md).
- [GolemBlue_LuongHoatDong.md](GolemBlue_LuongHoatDong.md).
- [GolemYellow_LuongHoatDong.md](GolemYellow_LuongHoatDong.md).
- [Golem_CameraPlayer.md](Golem_CameraPlayer.md).
- [ChienThang_QuaMan.md](ChienThang_QuaMan.md).
- [CayTrangTri_ThuTuHienThi.md](CayTrangTri_ThuTuHienThi.md).
- [SuaChanDuong_MidTree15.md](SuaChanDuong_MidTree15.md).

## 4. Phần cả hai bắt buộc nắm

Cả hai phải tự mở project và giải thích được những ý sau, kể cả không phải phần phụ trách chính:

| Nội dung chung | Câu trả lời cần nắm |
|---|---|
| Công cụ | Unity 6000.3.22f1, template Universal 2D, logic bằng Visual Scripting |
| Mục tiêu game | Sinh tồn, dùng cung chống enemy, đến cờ cuối map để thắng và chuyển màn |
| Phím | A/D hoặc Horizontal để di chuyển; Space nhảy; J bắn; K hướng dẫn |
| Script Machine | Component thực thi Script Graph trên GameObject |
| Flow và Data | Flow quyết định thứ tự thực hiện; Data truyền giá trị/đối tượng cho node |
| Object Variable | Dữ liệu riêng trên GameObject; ví dụ health của từng enemy |
| Graph / Scene / App Variables | Graph thuộc một instance graph; Scene thuộc scene; App tồn tại trong vòng đời ứng dụng và có thể giữ khi đổi scene |
| Rigidbody2D | Tham gia mô phỏng vật lý; vận tốc/trọng lực điều khiển chuyển động |
| Collider2D | Xác định vùng tương tác; Is Trigger nhận sự kiện chạm mà không tạo phản lực đẩy như collider thường |
| Animator | State chứa Motion/clip; parameter và transition điều khiển chuyển trạng thái |
| Prefab và Instantiate | Prefab là mẫu; Instantiate tạo đối tượng mới từ mẫu khi chạy |
| Thông số máu | Player 20; Skeleton 3; Golem Yellow 5; Golem Blue 9; mỗi đòn hợp lệ gây 1 sát thương |

Hai luồng giao tiếp cần cùng giải thích được:

```text
Enemy kiểm tra tầm đánh                 [Thành viên 2]
    → Trigger Custom Event PlayerTakeDamage
    → PlayerHealth nhận và trừ máu      [Thành viên 1]
    → Thanh đỏ giảm / xử lý Death
```

```text
Player tạo Arrow(Clone)                 [Thành viên 1]
    → Arrow có direction và vận tốc
    → Enemy nhận Trigger PlayerArrow    [Thành viên 2]
    → Hủy Arrow, trừ máu enemy, Hurt/Die
```

## 5. Chia phần GameUIManager dùng chung

GameUIManager là một graph chung, không cần tách thêm graph chỉ để chia việc:

| Khung | Người trình bày chính |
|---|---|
| 01 — Khởi tạo | Cả hai biết |
| 02 — K bật/tắt hướng dẫn | Thành viên 1 |
| 03 — Nút Đóng hướng dẫn | Thành viên 1 |
| 04 — Player chết/Game Over | Thành viên 1 |
| 05 — Chơi lại scene hiện tại | Thành viên 1 |
| 06 — Đến đích/Chiến thắng | Thành viên 2 |
| 07 — Qua màn mới | Thành viên 2 |

## 6. Trình tự demo đề xuất, khoảng 6–8 phút

1. **Cả hai — 30 giây:** giới thiệu game, công cụ, mục tiêu và phân công.
2. **Thành viên 1 — 2 phút:** demo di chuyển/nhảy, bắn hai hướng; mở Player_flip và ArrowFly để chỉ luồng chính.
3. **Thành viên 2 — 2 phút:** đưa enemy vào camera, chỉ luồng đuổi/đánh; bắn để enemy Hurt/Die; giải thích một graph mẫu rồi nêu khác biệt các loại.
4. **Thành viên 1 — 1 phút:** thanh máu, Game Over, Chơi lại, hướng dẫn K.
5. **Thành viên 2 — 1 phút:** FinishPoint, chiến thắng, chuyển Level2 và Scene List.

Nếu cần demo gần đích hoặc kiểm tra máu nhanh, thay giá trị trong Play hoặc dùng một bản scene demo riêng; giữ nguyên vị trí/máu khởi tạo của scene nộp.

## 7. Cách tự ôn trước buổi thi

Mỗi người tự làm được ba việc với phần mình: **demo kết quả**, **chỉ đúng GameObject/component/graph**, **giải thích một lượt Flow và các dây Data quan trọng**.

Sau đó đổi vai hỏi nhau: một người hỏi “sự kiện bắt đầu ở đâu?”, “giá trị này thuộc biến nào?”, “nếu bỏ dây này thì sao?”, người kia phải mở được vị trí tương ứng trong Unity để trả lời.

Chỉ đưa vào phần chức năng đã hoàn thiện những gì đang chạy trong project. Hiện bộ graph gameplay đang có là Player_flip, ArrowFly, PlayerHealth, SkeletonCombat, GolemBlueCombat, GolemYellowCombat, GameUIManager và FinishPoint. Bee có animation không đồng nghĩa đã có đầy đủ AI chiến đấu; kỹ năng đặc biệt và hệ sinh quái chỉ trình bày là hoàn thiện nếu nhóm đã bổ sung và kiểm tra được.

Các file có tên bắt đầu bằng dấu gạch dưới như `_GroundBlockingProbe` là công cụ kiểm tra tạm, không phải chức năng game để thuyết trình.
