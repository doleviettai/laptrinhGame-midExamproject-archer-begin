# Đến cuối map → Chiến thắng → Qua màn mới

Chức năng dùng Unity Editor và Visual Scripting, không có script C#. Tài liệu này mô tả các node và tham chiếu đã tạo trong project.

## 1. Kết quả và các file

- Màn đầu là `Assets/Scenes/SampleScene.unity`.
- Player chạm cờ xanh cuối map sẽ hiện bảng **CHIẾN THẮNG!** và game tạm dừng.
- Bấm **QUA MÀN MỚI** sẽ tải `Assets/Scenes/Level2.unity`, bắt đầu với 20 máu.
- Level2 dùng lại địa hình của màn đầu, đổi vị trí Skeleton/Golem và tông nền. Đây là màn 2 đơn giản để có thể chơi và chuyển scene thực tế.
- Đến đích ở Level2 hiện **HOÀN THÀNH!**, có nút **VỀ MÀN 1**.
- Nút Chơi lại của Game Over tải lại đúng scene đang chơi.
- Máu Golem vàng vẫn là 5, Golem xanh 9, Player tối đa 20.

| Thành phần | Vị trí |
|---|---|
| Cờ và vùng nhận Player | GameObject `FinishPoint`, có ở hai scene |
| Graph nhận chạm đích | `Assets/Script/FinishPoint.asset` |
| Bảng chiến thắng | GameObject `VictoryCanvas` |
| Nút chuyển màn | `VictoryCanvas/DimBackground/VictoryPanel/NextLevelButton` |
| Graph quản lý UI | `Assets/Script/GameUIManager.asset` |
| Ảnh cờ | `Assets/Asset/FinishFlag.png` |

## 2. Bước 1 — Đặt cờ và collider ở cuối map

Chọn **FinishPoint** trong Hierarchy của SampleScene hoặc Level2.

| Component / thuộc tính | Thiết lập |
|---|---|
| Transform Position | X = `108.5`, Y = `-6.24`, Z = `0` |
| Sprite Renderer | Sprite FinishFlag, dùng kiểu hiển thị pixel |
| Box Collider 2D | Enabled, **Is Trigger = True** |
| Collider Offset | X = `0`, Y = `2.5` |
| Collider Size | X = `1.8`, Y = `6` |
| Variables | Có Object Variable `GameUIManager` |
| Script Machine | Graph = `FinishPoint` |

Ground hiện kết thúc ở khoảng X = 111; cờ được đặt trước mép đất. Collider cao hơn hình cờ để nhận Player đi hoặc nhảy qua vùng đích.

Player đã có Rigidbody2D và Collider2D, Tag = **Player**, nên FinishPoint dùng collider tĩnh có Is Trigger để nhận sự kiện 2D. Không cần thêm Rigidbody2D lên cờ.

**Kiểm tra:** chọn FinishPoint, xem đường viền collider trong Scene và xác nhận vùng đích nằm trên đoạn đất cuối map. Nếu sau này kéo dài map, di chuyển FinishPoint đến cuối phần đất mới.

## 3. Bước 2 — Graph FinishPoint chỉ nhận Player

Chọn **FinishPoint > Script Machine > Edit Graph**. Khung:

**`01 | PLAYER CHAM CO DICH`**

Object Variable trên FinishPoint:

| Tên | Kiểu | Value |
|---|---|---|
| `GameUIManager` | GameObject | GameObject GameUIManager trong cùng scene |

Các node:

1. **On Trigger Enter 2D**, Target = This.
2. **Component Get Game Object**, đọc thuộc tính `gameObject`.
3. **Game Object Compare Tag**, Tag = `Player`.
4. **If**.
5. **Get Variable**, phạm vi Object, tên `GameUIManager`, Object mặc định This.
6. **Trigger Custom Event**, Name = `LevelCompleted`, Arguments = `0`.

### Dây Data

| Từ node/cổng | Đến node/cổng |
|---|---|
| On Trigger Enter 2D → Collider | Component Get Game Object → Target |
| Component Get Game Object → Value | Compare Tag → Target |
| Compare Tag → Result | If → Condition |
| Get Object Variable `GameUIManager` → Value | Trigger Custom Event → Target |

### Dây Flow — mũi tên trắng

```text
On Trigger Enter 2D
    → If đối tượng vừa chạm có Tag Player?
        True → Trigger Custom Event: LevelCompleted
```

False không nối tiếp: Arrow và enemy đi vào vùng này không mở bảng chiến thắng.

`This` ở graph FinishPoint nghĩa là GameObject FinishPoint. Biến GameUIManager ở đây thuộc FinishPoint, không phải biến có cùng tên trên Player.

## 4. Bước 3 — Tạo bảng VictoryCanvas

Chọn **VictoryCanvas**. Bảng này được tạo từ bố cục Game Over để giao diện đồng nhất, sau đó đổi chữ và nút.

| Component / thuộc tính | Giá trị |
|---|---|
| Canvas Render Mode | Screen Space - Overlay |
| Canvas Sort Order | `40` |
| Canvas Scaler | Scale With Screen Size |
| Reference Resolution | `1920 × 1080` |
| Match | `0.5` |
| Graphic Raycaster | Bật để nhận click |
| Trạng thái GameObject khi lưu scene | Tắt |

GameUIManager luôn bật để nhận sự kiện và bật Canvas khi cần. Không đặt graph quản lý UI lên Canvas bị tắt.

## 5. Bước 4 — Các biến mới trên GameUIManager

Chọn **GameUIManager > Variables**. Các biến sau đều có phạm vi **Object** trên GameUIManager:

| Tên chính xác | Kiểu | SampleScene | Level2 |
|---|---|---|---|
| `VictoryCanvas` | GameObject | VictoryCanvas | VictoryCanvas |
| `NextLevelButton` | GameObject | NextLevelButton | NextLevelButton |
| `hasWon` | Boolean | False | False |
| `NextScene` | String | `Level2` | `SampleScene` |

Các biến `Player`, `HelpCanvas`, `GameOverCanvas`, `RestartButton`, `CloseHelpButton` có sẵn được dùng lại.

`hasWon` ngăn xử lý chiến thắng lặp lại khi có nhiều lần chạm vùng đích. `NextScene` cho phép hai scene dùng chung graph mà vẫn chuyển đến scene khác nhau.

## 6. Bước 5 — Khởi tạo khi bắt đầu scene

Chọn **GameUIManager > Script Machine > Edit Graph**, khung:

**`01 | BAT DAU - AN CAC CANVAS`**

Flow:

```text
On Start
    → Time Set Time Scale = 1
    → HelpCanvas Set Active = False
    → GameOverCanvas Set Active = False
    → VictoryCanvas Set Active = False
    → Set Object Variable hasWon = False
```

Data mới:

- Get Variable, Object, `VictoryCanvas` → Target của **Game Object Set Active**, Value = False.
- Boolean Literal **False** → Value của **Set Variable**, Object, `hasWon`.

Các Get/Set Variable có Object mặc định This, nghĩa là GameUIManager.

**Kết quả:** khi vào màn mới hoặc chơi lại, game không giữ bảng chiến thắng và trạng thái thắng của lần trước.

## 7. Bước 6 — Nhận sự kiện LevelCompleted và hiện chiến thắng

Trong graph **GameUIManager**, khung:

**`06 | DEN DICH - CHIEN THANG`**

### Kiểm tra điều kiện

1. **Custom Event**: Name = `LevelCompleted`, Arguments = `0`, Target = This.
2. **Get Variable — Object — Player** để lấy GameObject Player.
3. **Get Variable — Object — isDead**, cổng Object lấy từ biến Player ở trên.
4. **If thứ nhất**, Condition lấy từ Player.isDead; dùng nhánh **False**.
5. **Get Variable — Object — hasWon**, Object = This.
6. **If thứ hai**, Condition lấy từ hasWon; dùng nhánh **False**.

Như vậy Player phải còn sống và chưa thắng màn này thì luồng mới tiếp tục.

### Hiện bảng và dừng nhân vật

```text
Custom Event: LevelCompleted
    → If Player.isDead?
        False → If hasWon?
            False → Set Object hasWon = True
                  → HelpCanvas Set Active = False
                  → GameOverCanvas Set Active = False
                  → VictoryCanvas Set Active = True
                  → Script Machine PlayerControls Set Enabled = False
                  → Rigidbody2D Player Set Linear Velocity = (0, 0)
                  → Time Set Time Scale = 0
```

### Data cần chú ý

| Nguồn | Đích |
|---|---|
| Boolean Literal True | Set Variable `hasWon` → Value |
| Get Object `HelpCanvas` | Target của Set Active False |
| Get Object `GameOverCanvas` | Target của Set Active False |
| Get Object `VictoryCanvas` | Target của Set Active True |
| Get Object `Player` | Object của Get Variable `PlayerControls` |
| Get Variable `PlayerControls` trên Player | Target của Script Machine Set Enabled False |
| Get Object `Player` | Target của Rigidbody2D Set Linear Velocity |

Chỉ tắt component điều khiển nhân vật. GameUIManager vẫn hoạt động để nhận click nút chuyển màn khi game đang tạm dừng.

## 8. Bước 7 — Nút Qua màn mới

Trong graph **GameUIManager**, khung:

**`07 | BUTTON QUA MAN MOI`**

Các node:

- **Get Variable**, Object, `NextLevelButton`.
- **On Button Click**, Target lấy từ NextLevelButton.
- **Time Set Time Scale**, giá trị `1`.
- **Get Variable**, Object, `NextScene`.
- **Scene Manager Load Scene**, overload nhận String `sceneName`.

Data:

```text
Get Object NextLevelButton → On Button Click: Target
Get Object NextScene       → Load Scene: Scene Name
```

Flow:

```text
On Button Click
    → Time Set Time Scale = 1
    → Scene Manager Load Scene
```

Đặt Time Scale về 1 trước khi tải scene để màn mới chạy bình thường. PlayerHealth của scene mới chạy On Start, đặt PlayerHealth bằng maxHealth là 20 và isDead = False.

## 9. Bước 8 — Chơi lại đúng scene hiện tại

Luồng Chơi lại trước đây nhập cố định `SampleScene`. Khi có thêm Level2, cách đó sẽ đưa người chơi về màn 1 nếu chết ở màn 2.

Mình đổi phần Data trong khung:

**`05 | CHOI LAI - LOAD SCENE HIEN TAI`**

Các node mới:

1. **Scene Manager Get Active Scene** — `SceneManager.GetActiveScene()`, không có tham số.
2. **Scene Get Name** — Get thuộc tính `name` của kiểu `UnityEngine.SceneManagement.Scene`.

Data:

```text
Scene Manager Get Active Scene → Result
    → Scene Get Name: Target
    → Name nối vào Scene Name của Load Scene
```

Flow giữ dạng:

```text
On Button Click của RestartButton
    → Time Set Time Scale = 1
    → Load Scene: tên scene đang chơi
```

Màn 1 chơi lại SampleScene; màn 2 chơi lại Level2.

## 10. Bước 9 — Chặn phím K sau khi thắng

Trong khung **02 | PHIM K - BAT / TAT HUONG DAN**, thêm **Get Variable Object hasWon** và **If** vào sau nhánh False của If isDead.

```text
On Update → If vừa nhấn K?
    True → If Player.isDead?
        False → If hasWon?
            False → Luồng bật/tắt hướng dẫn có sẵn
```

Khi đã thắng, hasWon = True, nên K không mở hướng dẫn và không bật lại thời gian trong lúc bảng chiến thắng đang hiện.

## 11. Bước 10 — Đăng ký scene trong Build Profiles

Mở **File > Build Profiles > Scene List**, kiểm tra hai scene được bật:

1. `Assets/Scenes/SampleScene.unity`.
2. `Assets/Scenes/Level2.unity`.

Hai scene đã được thêm vào `ProjectSettings/EditorBuildSettings.asset`. Chuỗi trong biến NextScene phải khớp tên scene, không kèm `.unity`.

## 12. Kiến thức bổ sung và cách tìm node

Các node On Trigger Enter 2D, Compare Tag, If, Get/Set Variable Object, Set Linear Velocity, Script Machine Set Enabled, Canvas, TextMeshPro, Button OnClick và Scene List thuộc nội dung bạn đã học hoặc yêu cầu trước.

Các phần sau là **kiến thức bổ sung**:

- **Component Get Game Object**: đọc `gameObject` từ Collider2D để kiểm tra Tag.
- **Custom Event / Trigger Custom Event**: gửi `LevelCompleted` từ cờ đến GameUIManager.
- **Game Object Set Active**: bật/tắt bảng UI.
- **Time Set Time Scale**: `0` để tạm dừng, `1` để chơi tiếp.
- **Scene Manager Get Active Scene** và **Scene Get Name**: đọc tên scene để chơi lại đúng màn.

Nếu tên tìm kiếm hiển thị khác cách viết trong tài liệu, tìm member `SetActive`, `timeScale`, `GetActiveScene`, `LoadScene`, hoặc `name`, rồi chọn đúng kiểu GameObject, Time, SceneManager hoặc Scene như đã nêu. Các node này đã được ghi trong graph hiện tại.

## 13. Kiểm tra kết quả

1. Play SampleScene; bảng chiến thắng phải ẩn khi bắt đầu.
2. Đi tới cờ xanh cuối map, khoảng X = 108.5: hiện CHIẾN THẮNG và nút QUA MÀN MỚI.
3. Bấm nút: chuyển sang Level2, có chữ MÀN 2 trên HUD, máu đầy và game tiếp tục.
4. Chết ở màn 2 rồi bấm Chơi lại: vẫn ở Level2.
5. Đến cờ cuối Level2: hiện HOÀN THÀNH và nút VỀ MÀN 1.

Để kiểm tra nhanh bằng Editor, chỉ thay đổi Transform của Player **trong lúc Play**, đưa X về gần 108.5, Y khoảng -3 để Player rơi vào vùng cờ. Thoát Play sẽ trả vị trí về bản đã lưu. Không lưu vị trí kiểm thử này vào màn chính.

**Đã kiểm thử:** dùng bản scene tạm đặt Player gần cờ, xác nhận Trigger hiện bảng chiến thắng, bấm nút chuyển được sang Level2; bật Game Over tạm trong Play ở Level2 để kiểm tra nút Chơi lại tải lại đúng Level2. Lỗi xuống dòng YAML phát hiện trong quá trình kiểm tra đã được sửa và lần nạp lại không báo lỗi đó. Chưa chạy bộ kiểm thử đi bộ từ đầu đến cuối toàn bộ hai map.

## 14. Cách giải thích ngắn với giáo viên

> Em đặt một Box Collider 2D có Is Trigger ở cờ cuối màn. Khi đối tượng chạm cờ có Tag Player, graph gửi sự kiện LevelCompleted đến GameUIManager. Manager kiểm tra Player còn sống và chưa thắng, rồi bật bảng chiến thắng, tắt điều khiển và tạm dừng. Nút Qua màn mới đặt Time Scale về 1 và tải scene được ghi trong Object Variable NextScene. Mỗi scene có giá trị NextScene riêng. Nút Chơi lại đọc tên scene đang chơi để tải lại đúng màn đó.
