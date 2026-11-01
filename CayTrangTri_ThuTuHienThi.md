# Sửa cây trang trí che Player và enemy

Tài liệu này mô tả phần sửa hình ảnh bị cây che. Với trường hợp bị cản di chuyển gần `MidTree_15`, kết quả kiểm tra vật lý và cách sửa nằm trong [SuaChanDuong_MidTree15.md](SuaChanDuong_MidTree15.md).

## Lỗi nằm ở đâu?

Trong cả `SampleScene` và `Level2`, mở Hierarchy:

```text
Backdrop
└── EnvironmentDecor
    └── ForegroundTrees
        └── FrontTree_...
```

Có 9 cây trong nhóm này: `FrontTree_00`, `01`, `02`, `03`, `05`, `06`, `07`, `08`, `09`.

Trước khi sửa, component **Sprite Renderer > Additional Settings** của các cây đặt **Sorting Layer = Foreground**, **Order in Layer = 2**. Trong Project Settings > Tags and Layers, thứ tự Sorting Layers là Default → Player → Enemy → Foreground. Vì vậy cây được vẽ sau cùng và che lên hình Player/enemy, tạo cảm giác có vật chắn trước nhân vật.

Order in Layer chỉ so sánh trong cùng một Sorting Layer. Chỉ tăng Order của Player hoặc enemy không giải quyết việc cây nằm ở Sorting Layer Foreground cao hơn.

## Đã sửa thế nào?

Đổi Sprite Renderer của 9 cây trên ở mỗi scene:

| Thuộc tính | Trước | Sau |
|---|---|---|
| Sorting Layer | Foreground | **Default** |
| Order in Layer | 2 | **-5** |

Các cây FarTrees đang ở Default/-7, MidTrees ở Default/-6. Sau sửa, thứ tự cây từ xa đến gần là FarTrees → MidTrees → nhóm cây vừa sửa, rồi đến các Sorting Layer Player và Enemy. Nhờ đó nhân vật hiện phía trước các cây trang trí.

Nhóm vẫn giữ tên ForegroundTrees để dễ tìm lại vị trí cũ; vị trí, kích thước và sprite cây được giữ nguyên.

## Có collider chắn đường không?

Đã kiểm tra toàn bộ 45 sprite cây trong EnvironmentDecor ở từng scene: các cây chỉ có **Transform** và **Sprite Renderer**, không có Collider hay Rigidbody. Vì vậy các cây này không tạo va chạm chặn đường. Lỗi được xác định ở thứ tự vẽ hình.

## Cách tự kiểm tra trong Editor

1. Mở SampleScene hoặc Level2.
2. Chọn một cây ở `Backdrop/EnvironmentDecor/ForegroundTrees`.
3. Xem **Sprite Renderer > Additional Settings**: Sorting Layer phải là Default, Order in Layer là -5.
4. Quan sát Game view khi Player hoặc enemy ở cùng vị trí trên hình với thân cây: hình nhân vật phải nằm trước cây.

Không cần thêm component, node hoặc thay graph điều khiển nhân vật để sửa lỗi hiển thị này.

Bản sao scene trước khi sửa và danh sách Sprite Renderer đã thay được lưu trong `Backups/EnvironmentDecorSorting/20261101_164124/`.
