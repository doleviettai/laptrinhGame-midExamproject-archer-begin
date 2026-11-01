# Thanh máu đỏ của Player — luồng xử lý bằng Visual Scripting

Tài liệu này mô tả đúng phần đã nối trong project Archer Survival. Toàn bộ hành vi dùng Script Graph và component Unity, không có script C#.

## 1. Kết quả cần đạt và vị trí thực hiện

- Player có tối đa **20 máu**; mỗi đòn đánh hợp lệ của enemy làm mất **1 máu**.
- Thanh đỏ hiển thị tỷ lệ **máu hiện tại / máu tối đa**.
- Hết máu thì thanh đỏ rỗng; Player chạy luồng Death có sẵn.
- Golem vàng giữ **5 máu**, Golem xanh giữ **9 máu**.

| Thành phần | Vị trí trong project hoặc Hierarchy |
|---|---|
| Scene | `Assets/Scenes/SampleScene.unity` |
| GameObject chứa xử lý máu | `Player` |
| Component chạy graph | Script Machine đang gán graph `PlayerHealth` |
| File graph | `Assets/Script/PlayerHealth.asset` |
| GameObject thanh đỏ | `Canvas > Info > HealthBar > Fill` |
| Component được cập nhật | **Image** trên `Fill` |
| Khung mới trong graph | `04 \| THANH MAU DO - PlayerHealth / maxHealth` |

Trên Player đã có Variables và Script Machine xử lý máu, nên mình dùng lại các component này. Không cần thêm một Script Machine khác lên Canvas hoặc Fill.

## 2. Bước 1 — Kiểm tra Image của thanh đỏ

1. Trong Hierarchy, chọn **Canvas > Info > HealthBar > Fill**.
2. Tại component **Image**, kiểm tra các giá trị:

| Thuộc tính | Giá trị |
|---|---|
| Source Image | Sprite thanh đỏ bạn đã chọn |
| Image Type | **Filled** |
| Fill Method | **Horizontal** |
| Fill Origin | **Left** |
| Fill Amount ban đầu | **1** |

Các thiết lập trên đã có trong scene lúc mình kiểm tra. Mình nối vào Image này để sử dụng thanh máu bạn đã dựng.

**Cách kiểm tra riêng Image:** khi chưa Play, kéo thử Fill Amount từ `1` xuống `0.5`. Phần đỏ phải còn một nửa, giữ đầu bên trái và thu đầu bên phải vào. Sau đó trả lại `1`.

## 3. Bước 2 — Chuẩn bị các biến trên Player

Chọn **Player > Variables**. Các biến dưới đây đều có phạm vi **Object**, thuộc GameObject Player; không phải Graph, Scene hoặc App.

| Tên biến chính xác | Kiểu | Giá trị hoặc tham chiếu | Công dụng |
|---|---|---|---|
| `PlayerHealth` | Integer | `20` | Máu hiện tại |
| `maxHealth` | Integer | `20` | Máu tối đa, dùng khi khởi tạo và tính tỷ lệ |
| `HealthBarFill` | Image — `UnityEngine.UI.Image` | Component Image của `Canvas/Info/HealthBar/Fill` | Chỉ ra Image cần giảm Fill Amount |
| `isDead` | Boolean | `False` | Trạng thái chết đang dùng trong graph |
| `PlayerControls` | Script Machine | Script Machine điều khiển Player đang có | Dùng để tắt điều khiển khi chết |

**Phần mình thay đổi:** giữ `PlayerHealth = 20` theo bạn đã đặt, sửa `maxHealth` từ `15` thành `20`, thêm biến `HealthBarFill` và gán Image của Fill vào biến đó. Hai biến `isDead` và `PlayerControls` được dùng lại.

Nếu cần gán lại `HealthBarFill` bằng Editor: chọn kiểu Image cho biến, sau đó kéo **component Image** ở Inspector của Fill vào ô Value. Biến phải tham chiếu thanh đỏ **Fill**, không phải ảnh viền **Background**.

## 4. Bước 3 — Khởi tạo máu theo maxHealth

Chọn **Player > Script Machine có graph PlayerHealth > Edit Graph**.

Trước đó, On Start vẫn có Integer `15` nối vào Set Variable `PlayerHealth`. Vì vậy, dù Inspector đặt PlayerHealth là `20`, khi chạy game graph vẫn ghi đè về `15`.

Mình thay nguồn dữ liệu `15` bằng **Get Variable**, phạm vi **Object**, tên **`maxHealth`**.

### Dây Flow — mũi tên trắng

```text
On Start
    → Set Variable (Object, PlayerHealth)
    → Set Variable (Object, isDead)
```

### Dây Data

| Từ node/cổng | Đến node/cổng |
|---|---|
| Get Variable `maxHealth` → Value | Set Variable `PlayerHealth` → Value |
| Boolean `False` → Output | Set Variable `isDead` → Value |

Các node biến ở đây thao tác trên **This**, tức Player đang chạy Script Machine.

**Kết quả:** mỗi lần scene bắt đầu, PlayerHealth được lấy từ maxHealth. Hiện maxHealth là `20`, nên Player bắt đầu với `20` máu. Lần sau muốn đổi máu tối đa, bạn chỉnh Object Variable `maxHealth` trên Player.

## 5. Bước 4 — Dùng lại luồng enemy gây sát thương

Phần trừ máu đã có trong graph, mình giữ để thanh đỏ đọc đúng cùng một biến máu.

Skeleton, Golem Blue và Golem Yellow đang gửi sự kiện **`PlayerTakeDamage`** đến Player khi đòn đánh đủ điều kiện gây sát thương. PlayerHealth nhận sự kiện bằng **Custom Event**, tên chính xác `PlayerTakeDamage`, không có đối số.

### Dây Data và điều kiện

1. **Get Variable — Object — `PlayerHealth`** nối vào A của **Greater**; B là Integer `0`.
2. Kết quả Greater nối vào Condition của **If thứ nhất**.
3. Get Variable `PlayerHealth` nối vào A của **Subtract**; B là Integer `1`.
4. Kết quả Subtract nối vào Value của **Set Variable — Object — `PlayerHealth`**.
5. Output của Set Variable vừa cập nhật nối vào A của **Greater thứ hai**; B là `0`.
6. Kết quả Greater thứ hai nối vào Condition của **If thứ hai**.

### Dây Flow — mũi tên trắng

```text
Custom Event: PlayerTakeDamage
    → If thứ nhất: PlayerHealth > 0?
        True → Set Variable PlayerHealth = PlayerHealth - 1
             → If thứ hai: máu sau khi trừ > 0?
                 True  → Animator Set Trigger: isEatHit
                 False → Luồng chết có sẵn
```

Nhánh False của If thứ nhất không thực hiện thêm việc gì: Player đã hết máu thì sự kiện sau đó không tiếp tục trừ máu.

**Ví dụ:** đang có `20` máu, enemy đánh trúng một đòn hợp lệ thì Set Variable ghi lại `19`. Còn máu nên Animator nhận trigger `isEatHit` để chạy animation bị đánh. Mỗi sự kiện sát thương hợp lệ trừ đúng `1` máu.

## 6. Bước 5 — Thêm khung cập nhật thanh đỏ

Vẫn trong graph **PlayerHealth** trên **Player**, tìm khung mới:

**`04 | THANH MAU DO - PlayerHealth / maxHealth`**

Khung này có các node:

| Node cần tìm | Thiết lập |
|---|---|
| **This** | Player đang chạy graph; khung này dùng một This riêng |
| **Get Variable** | Object, tên `PlayerHealth` |
| **Get Variable** | Object, tên `maxHealth` |
| **Get Variable** | Object, tên `HealthBarFill` |
| **Divide** | Chọn bản thuộc **Math > Scalar**, xử lý số thực |
| **On Update** | Cập nhật mỗi frame |
| **Image Set Fill Amount** | Property `fillAmount` của `UnityEngine.UI.Image` |

Khi tìm node Image, nhập **`Image Set Fill Amount`** hoặc **`fillAmount`**, rồi chọn node **Set** của component **UnityEngine.UI.Image**. Không chọn node Get Fill Amount.

### Nối Data — đọc biến và tính tỷ lệ

| Từ node/cổng | Đến node/cổng |
|---|---|
| This → Self | Get Variable `PlayerHealth` → Object |
| This → Self | Get Variable `maxHealth` → Object |
| This → Self | Get Variable `HealthBarFill` → Object |
| Get Variable `PlayerHealth` → Value | Divide → A, tử số |
| Get Variable `maxHealth` → Value | Divide → B, mẫu số |
| Divide → A ÷ B | Image Set Fill Amount → Fill Amount |
| Get Variable `HealthBarFill` → Value | Image Set Fill Amount → Target |

Ba dây từ This đều nằm trong khung này, giúp nhìn rõ các biến đang thuộc Player.

### Nối Flow — thực hiện cập nhật Image

```text
On Update → Image Set Fill Amount
```

Dây trắng chỉ có nhiệm vụ yêu cầu cập nhật Image. Khi node Set Fill Amount chạy, nó lấy Image từ HealthBarFill và lấy giá trị từ phép chia.

### Vì sao dùng Divide thuộc Math > Scalar?

Fill Amount cần số thực trong khoảng `0` đến `1`. Bản Scalar Divide chuyển các giá trị đầu vào sang số thực để tính tỷ lệ, nên `19 / 20` cho kết quả `0.95`.

Không dùng phép chia chỉ xử lý Integer cho tỷ lệ này, vì phần lẻ có thể bị mất.

| PlayerHealth | maxHealth | Fill Amount | Phần đỏ còn lại |
|---:|---:|---:|---:|
| 20 | 20 | 1 | 100% |
| 19 | 20 | 0.95 | 95% |
| 15 | 20 | 0.75 | 75% |
| 10 | 20 | 0.5 | 50% |
| 1 | 20 | 0.05 | 5% |
| 0 | 20 | 0 | 0% |

Thanh máu đọc PlayerHealth mỗi frame, nên sau khi luồng sát thương đổi máu, nó hiển thị tỷ lệ mới ở lần cập nhật tiếp theo.

## 7. Bước 6 — Khi Player hết máu

Luồng chết có sẵn trong PlayerHealth tiếp tục được sử dụng:

```text
If máu sau khi trừ > 0: False
    → Set Object isDead = True
    → Animator Play: Death
    → Rigidbody2D Set Linear Velocity = (0, 0)
    → Rigidbody2D Set Gravity Scale = 0
    → Box Collider 2D Set Enabled = False
    → Script Machine điều khiển Player: Set Enabled = False
```

Script Machine bị tắt ở cuối là component được biến **PlayerControls** tham chiếu. Script Machine **PlayerHealth** vẫn hoạt động, nên phần cập nhật thanh đỏ vẫn có thể đưa Fill Amount về `0`.

## 8. Bước 7 — Kiểm tra trong Unity

1. Lưu scene. Nếu Unity đang hỏi nạp lại scene sau thay đổi từ file, chọn **Reload**.
2. Chọn Player, xem Variables để biết vị trí `PlayerHealth`, `maxHealth` và `HealthBarFill`.
3. Bấm Play: `PlayerHealth = 20`, `maxHealth = 20`; thanh đỏ phải đầy.
4. Để Skeleton hoặc Golem đánh trúng một lần: PlayerHealth phải từ `20` xuống `19`, thanh đỏ còn `95%` và Player chạy Hurt.
5. Có thể tạm sửa **PlayerHealth trong lúc Play** thành `10` để kiểm tra riêng việc hiển thị: thanh đỏ phải còn một nửa. Thao tác này chỉ đổi biến, không tự gửi sự kiện gây sát thương hoặc chạy luồng chết.
6. Để kiểm tra Death, đặt PlayerHealth là `1` trong Play rồi để enemy đánh một đòn hợp lệ: máu về `0`, thanh đỏ rỗng và luồng Death chạy.
7. Thoát Play, chạy lại: On Start phải khôi phục máu theo maxHealth là `20`.

**Trạng thái xác minh khi viết tài liệu:** đã đọc lại graph và scene trên đĩa, xác nhận các node, dây nối, tham chiếu Image và giá trị biến như mô tả. Chưa xác nhận kết quả trong Play vì lượt điều khiển Unity trước đã được dừng bằng phím Esc.

## 9. Nội dung thuộc kiến thức bổ sung

- **This:** trả về GameObject đang chạy graph; ở đây là Player. Tìm node bằng từ khóa **This**.
- **Custom Event / Trigger Custom Event:** dùng để gửi và nhận `PlayerTakeDamage` giữa enemy và Player. Đây là luồng sát thương có sẵn được dùng lại.

On Start, On Update, Get/Set Variable Object, Greater, If, Subtract, Divide, Image Set Fill Amount và các node dừng nhân vật thuộc nhóm kiến thức bạn đã liệt kê. Phần thanh đỏ mới chỉ cần đọc biến, chia tỷ lệ và đặt Fill Amount.

## 10. Cách trình bày ngắn khi giáo viên hỏi

> Em lưu máu hiện tại và máu tối đa bằng Object Variables trên Player. Khi bắt đầu, em đặt máu hiện tại bằng máu tối đa là 20. Enemy đánh trúng thì gửi sự kiện PlayerTakeDamage; Player nhận sự kiện và trừ một máu. Mỗi frame, em lấy máu hiện tại chia máu tối đa bằng Divide số thực, rồi gán kết quả vào Fill Amount của Image thanh đỏ. Nếu máu bằng không thì chạy Death và tắt điều khiển.
