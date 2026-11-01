# Sửa nhân vật bị chặn gần MidTree_15

## Nguyên nhân được kiểm tra trong Play

`Backdrop/EnvironmentDecor/MidTrees/MidTree_15` ở X = 86.55 chỉ có Transform và Sprite Renderer. Toàn bộ Backdrop không có collider tạo va chạm vật lý.

Vật va chạm với Player tại đoạn này là **Enemy/Golem_blue > Box Collider 2D**. Trước khi sửa, Player và các enemy đều dùng physics Layer Default; ma trận Physics 2D cho phép chúng va chạm, nên hai Rigidbody2D có thể cản/đẩy nhau khi gặp nhau.

Lần sửa trước đổi Sorting Layer của cây tiền cảnh chỉ giải quyết việc cây che hình. Sorting Layer không điều khiển va chạm vật lý. Vấn đề ở MidTree_15 được kiểm tra riêng lần này.

## Bằng chứng tái hiện

Dùng một scene thử nghiệm riêng, đặt Player tại X = 83.2 và cho vận tốc X = 7 bằng các node Visual Scripting. Các phép đo không thay đổi graph điều khiển chính.

| Lượt kiểm tra | Kết quả |
|---|---|
| Tắt enemy, đi sang phải | Qua vị trí cây 86.55, đến khoảng X = 100.02 |
| Tắt enemy, đi sang trái từ X = 88 | Đi qua cây về bên trái |
| Bật enemy như scene chính, trước sửa | On Collision Enter 2D ghi nhận `Golem_blue`; vận tốc bị cản/đẩy, vị trí sau cùng khoảng X = 93.29 |
| Bật enemy, sau sửa | Không còn va chạm thân Player–Golem; đi đến khoảng X = 100.04 |
| Sát thương enemy sau sửa | Máu Player giảm 20 → 19 |
| Một mũi tên thật trúng Golem sau sửa | Máu Golem Blue giảm 9 → 8 |

Phép đo tập trung đoạn gần MidTree_15; không thay thế kiểm thử toàn bộ địa hình từ đầu đến cuối màn.

## Cách đã sửa bằng Editor settings

### 1. Tạo hai physics Layer

Vào **Edit > Project Settings > Tags and Layers**, phần **Layers**:

| Vị trí | Tên |
|---|---|
| User Layer 8 | `PlayerBody` |
| User Layer 9 | `EnemyBody` |

Đây là ô **Layer** ở đầu Inspector của GameObject. Nó khác với **Sorting Layer** trong Sprite Renderer.

### 2. Gán Layer cho các đối tượng

Đã áp dụng trong **SampleScene** và **Level2**:

| GameObject | Layer |
|---|---|
| Player | PlayerBody |
| Enemy/Skeleton | EnemyBody |
| Enemy/Golem_blue | EnemyBody |
| Enemy/Golem_yellow | EnemyBody |
| Enemy/Bee | EnemyBody |

Chỉ cần gán GameObject có collider thân nhân vật. Các Tag Player, Enemy và PlayerArrow tiếp tục phục vụ Compare Tag.

### 3. Bỏ va chạm thân nhân vật

Vào **Edit > Project Settings > Physics 2D > Layer Collision Matrix**:

| Cặp Layer | Trạng thái |
|---|---|
| PlayerBody – EnemyBody | Bỏ chọn |
| EnemyBody – EnemyBody | Bỏ chọn |
| PlayerBody – Ground | Giữ chọn |
| EnemyBody – Ground | Giữ chọn |
| Default – EnemyBody | Giữ chọn: Arrow prefab hiện ở Default |
| Default – PlayerBody | Giữ chọn: vùng FinishPoint hiện ở Default |

Kết quả là Player và enemy có thể đi qua thân nhau; enemy cũng không đẩy hoặc chặn đường nhau. Cả hai vẫn đứng trên Ground. Collider của enemy vẫn nhận mũi tên.

Không đổi Box Collider 2D thành Is Trigger cho thân enemy, vì collider này vẫn cần để enemy đứng trên đất.

## Vì sao enemy vẫn gây sát thương?

Các graph SkeletonCombat, GolemBlueCombat và GolemYellowCombat hiện kiểm tra khoảng cách/tầm đánh, dùng Timer rồi gửi `PlayerTakeDamage` đến Player. Chúng không cần va chạm thân để thực hiện đòn đánh.

Mũi tên dùng collider có Is Trigger và kiểm tra Tag PlayerArrow trên enemy graph. Cặp physics Layer Default–EnemyBody vẫn cho phép nhận trigger; phép thử thực tế xác nhận Golem Blue mất một máu.

## File đã thay đổi

- `ProjectSettings/TagManager.asset`: thêm tên PlayerBody và EnemyBody.
- `ProjectSettings/Physics2DSettings.asset`: tắt hai cặp va chạm thân ở trên.
- `Assets/Scenes/SampleScene.unity`: gán Layer cho Player và enemy.
- `Assets/Scenes/Level2.unity`: gán Layer tương tự.

Không thêm C# hoặc node vào graph gameplay để sửa va chạm này. Scene và graph chẩn đoán tạm được chuyển vào Backups sau khi kiểm tra.

## Kiến thức bổ sung

**Physics Layer** và **Physics 2D Layer Collision Matrix** là kiến thức bổ sung so với danh sách node đã học. Chúng là thiết lập sẵn có của Unity Editor.

Khi trình bày với giáo viên có thể nói: “Em tách Layer thân Player và enemy để chúng không cản nhau. Enemy vẫn gây sát thương bằng kiểm tra tầm đánh trong Visual Scripting; mũi tên vẫn tương tác với collider enemy.”
