# Player Jump - Space

GameObject: Player. Dùng Script Machine có sẵn, graph Player_flip.
Giữ Rigidbody 2D (Dynamic), Box Collider 2D (Is Trigger = false), Freeze Rotation Z.
Rigidbody 2D Gravity Scale = 3.
Biến Object: jumpSpeed, Float, giá trị 14.

## Flow (mũi tên trắng)

On Update → If (Get Key Down, Key = Space).
Nhánh True → If (Get Linear Velocity Y > 0.1).
Nhánh False của điều kiện đang bay lên → If (normal.y > 0.5).
Nhánh True của điều kiện mặt đất → Rigidbody 2D: Set Linear Velocity.

## Data

Input: Get Key Down (KeyCode), Key = Space → If đầu tiên, Condition.
Rigidbody 2D: Get Linear Velocity Y → Greater, A; B = 0.1 → If thứ hai, Condition.
Box Collider 2D: Get Bounds → Bounds: Get Center → Physics 2D: Raycast, Origin.
Box Collider 2D: Get Bounds → Bounds: Get Extents → Vector 3: Get Y → Add (Math/Scalar), input 0.
Add input 1 = 0.1 → Physics 2D: Raycast, Distance.
Raycast: Direction = (0, -1); Layer Mask = 64 (Ground ở layer 6); Min Depth = -1000; Max Depth = 1000.
Physics 2D: Raycast → Raycast Hit 2D: Get Normal → Vector 2: Get Y → Greater, A; B = 0.5 → If kiểm tra mặt đất, Condition.
Rigidbody 2D: Get Linear Velocity X → Vector 2: Create, X.
Get Object Variable jumpSpeed → Vector 2: Create, Y.
Vector 2: Create → Rigidbody 2D: Set Linear Velocity, Value.
Các Target Rigidbody/BoxCollider để Self: lấy component trên Player.
Bounds Center (Vector3) được Visual Scripting chuyển sang Vector2 khi nối Origin.

## Kiến thức bổ sung

Input Get Key Down (Space), Vector2 Create và đọc vận tốc X/Y; Bounds, Add, Physics2D Raycast, RaycastHit2D Normal và Ground physics layer.
Các member được xác minh bằng tài liệu XML Unity cài trên máy; các cổng node bằng mã nguồn package Visual Scripting 1.9.12.
Tên hiển thị trong tìm kiếm có thể khác cách viết hoa/khoảng trắng; nhóm node đã được nối sẵn trong graph.

## Kiểm tra bằng Unity

1. Mở Player → Script Machine → Edit Graph; tìm nhóm Player Jump - Space.
2. Play, bấm vào cửa sổ Game để nhận bàn phím.
3. Space trên đất: nhảy lên rồi rơi xuống. Giữ Space không tự nhảy lặp.
4. Space liên tục khi đang bay: không nhảy thêm.
5. Vừa A/D hoặc mũi tên trái/phải vừa Space: tiếp tục di chuyển ngang.
6. J vẫn kích hoạt tấn công.
7. Đáp xuống đất, thả rồi bấm lại Space: nhảy tiếp.
8. Mặt đứng của tường hoặc đỉnh quỹ đạo khi bay không cho nhảy thêm.

Không tạo clip hay state Jump do bộ asset không có frame nhảy.
Kiểm tra chạm đất dùng một tia ở giữa collider; cần tâm collider còn nằm trên bề mặt đất.
Tốc độ nhảy 14, trọng lực 3 tương ứng độ cao lý thuyết khoảng 3.33 Unity units.

Nếu scene/graph đang mở chưa tải thay đổi: trở về Unity và chấp nhận Reload khi Unity hỏi.
Nếu Unity hỏi lưu scene cũ đang mở, không ghi đè lên bản đã chỉnh trên đĩa; mở lại Assets/Scenes/SampleScene.unity.

Bản sao trước khi sửa nằm tại Backups/PlayerJump (ngoài Assets).
