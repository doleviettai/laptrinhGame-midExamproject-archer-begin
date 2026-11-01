param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$root = 'D:\GamePrograms\MidTestExam'
$asset = Join-Path $root 'Assets\Script\GolemBlueCombat.asset'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$raw = [IO.File]::ReadAllText($asset, $utf8)
$originalHash = (Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash
$match = [regex]::Match($raw, "    _json: '([\s\S]*?)'\r?\n    _objectReferences:")
if (-not $match.Success) { throw 'Cannot find embedded graph JSON.' }
$json = ($match.Groups[1].Value -replace '\r?\n[ ]+', ' ').Replace("''", "'")
$payload = $json | ConvertFrom-Json
$graph = $payload.graph
$nodes = @($graph.elements | Where-Object { $_.'$type' -notmatch 'Connection$|GraphGroup$' })
$connections = @($graph.elements | Where-Object { $_.'$type' -match 'Connection$' })
$oldGroups = @($graph.elements | Where-Object { $_.'$type' -match 'GraphGroup$' })
if ($oldGroups.Count -gt 0) { throw 'Groups already exist; inspect them before arranging again.' }

# Keep the existing element order, IDs, GUIDs, values, and connections intact.
function Get-ElementMeaning($element) {
    $meaning = [ordered]@{}
    foreach ($property in $element.PSObject.Properties) {
        if ($property.Name -ne 'position') { $meaning[$property.Name] = $property.Value }
    }
    return ($meaning | ConvertTo-Json -Depth 100 -Compress)
}
$meaningBefore = @{}
$nodesById = @{}
foreach ($element in $graph.elements) {
    $meaningBefore[[string]$element.guid] = Get-ElementMeaning $element
}
foreach ($node in $nodes) { $nodesById[[string]$node.'$id'] = $node }
$orderBefore = @($graph.elements | ForEach-Object { [string]$_.guid })

# The node IDs below belong to the complete graph saved by the user.
# Check stable GUIDs on the three event branches before applying this layout.
if ($nodesById['9'].guid -ne 'af99c823-251d-451d-a781-b4a737dd84e1') { throw 'Start node changed.' }
if ($nodesById['141'].guid -ne '6991fff9-2006-4c7c-8f55-b03541ba5c75') { throw 'Trigger event changed.' }
if ($nodesById['201'].guid -ne 'f768c63b-18a2-4423-8eb6-fce9b32c90bb') { throw 'Complete death branch is missing.' }

$groups = New-Object 'System.Collections.Generic.List[object]'
$assigned = @{}
$membership = New-Object 'System.Collections.Generic.List[object]'
function Add-Section($label, $comment, $rect, $color, $placements) {
    foreach ($place in $placements) {
        $id = [string]$place[0]
        if (-not $nodesById.ContainsKey($id)) { throw "Unknown node $id in $label" }
        if ($assigned.ContainsKey($id)) { throw "Node $id assigned twice." }
        $node = $nodesById[$id]
        $node.position.x = [double]$place[1]
        $node.position.y = [double]$place[2]
        if ($node.position.x -lt $rect[0] -or $node.position.x + 280 -gt $rect[2] -or
            $node.position.y -lt $rect[1] + 90 -or $node.position.y + 130 -gt $rect[3]) {
            throw "Node $id lies outside the section $label."
        }
        $assigned[$id] = $label
        $membership.Add([pscustomobject]@{ nodeGuid=$node.guid; nodeId=$id; section=$label })
    }
    $groups.Add([pscustomobject][ordered]@{
        position=[pscustomobject][ordered]@{
            xMin=[double]$rect[0]; yMin=[double]$rect[1]; xMax=[double]$rect[2]; yMax=[double]$rect[3]
        }
        label=$label
        comment=$comment
        color=[pscustomobject][ordered]@{ r=[double]$color[0]; g=[double]$color[1]; b=[double]$color[2]; a=1.0 }
        guid=[guid]::NewGuid().ToString()
        '$version'='A'
        '$type'='Unity.VisualScripting.GraphGroup'
    })
}

Add-Section '01 | KHỞI TẠO' `
    'On Start đặt health = 7, isAttacking = False, isHurt = False. Các biến đều thuộc Object trên Golem Blue.' `
    @(0,0,1500,650) @(0.13,0.30,0.20) @(
        @('9',70,170), @('80',360,170), @('82',360,430),
        @('23',730,170), @('25',730,430), @('64',1100,170), @('66',1100,430)
    )
Add-Section '02 | PHÁT HIỆN PLAYER' `
    'On Became Visible → đặt Object isAwake = True. Sự kiện cũng có thể được kích hoạt bởi camera Scene view trong Editor.' `
    @(1700,0,2800,650) @(0.10,0.29,0.31) @(
        @('84',1770,170), @('86',2380,170), @('88',2100,430)
    )
Add-Section '03 | HƯỚNG VÀ KHOẢNG CÁCH' `
    'Data dùng chung: deltaX = Player.position.x − This.position.x. deltaX > 0: Player bên phải. Abs(deltaX) ≤ attackRange: trong tầm ngang. Kết quả cấp cho nhóm 04, 05 và 07.' `
    @(3000,0,6300,850) @(0.10,0.23,0.36) @(
        @('102',3070,180), @('53',3410,180), @('94',3750,180),
        @('97',3410,480), @('11',3750,480), @('108',4090,320),
        @('197',4470,180), @('90',4470,480), @('72',4810,650), @('35',5180,480)
    )
Add-Section '04 | CHỌN HÀNH VI' `
    'On Update → If isAwake → If isHurt. Hurt=True: nhóm 08. Hurt=False: kiểm tra tầm đánh; ngoài tầm → nhóm 05, trong tầm → nhóm 06.' `
    @(0,1100,1500,1900) @(0.18,0.25,0.35) @(
        @('78',70,1290), @('129',80,1560), @('148',450,1290),
        @('68',450,1560), @('76',820,1290), @('14',1170,1290)
    )
Add-Section '05 | ĐUỔI VÀ QUAY MẶT' `
    'If deltaX > 0: vận tốc X = moveSpeed, Flip X=False, isWalk=True. Nhánh còn lại: vận tốc X = moveSpeed × −1, Flip X=True, isWalk=True. Giữ nguyên vận tốc Y.' `
    @(1700,1100,3700,1980) @(0.10,0.31,0.22) @(
        @('127',1770,1440), @('123',1790,1740),
        @('131',2120,1280), @('113',2540,1280), @('60',2960,1280),
        @('152',2120,1780), @('116',2440,1570), @('110',2860,1570), @('119',3280,1570)
    )
Add-Section '06 | BẮT ĐẦU ĐÒN ĐÁNH' `
    'Trong tầm: dừng X, isWalk=False. If isAttacking=False → đặt True → Animator doAttack → Timer attackDelay. If isAttacking=True: không khởi động lại đòn.' `
    @(3900,1100,6300,1980) @(0.35,0.24,0.08) @(
        @('16',3970,1290), @('19',4300,1290), @('27',4300,1580),
        @('45',4650,1290), @('29',4930,1290), @('33',4930,1580),
        @('47',5350,1290), @('70',5390,1720), @('37',5760,1250)
    )
Add-Section '07 | GÂY SÁT THƯƠNG VÀ NGHỈ' `
    'Timer ra đòn Completed → kiểm tra lại tầm ngang. True: gửi PlayerTakeDamage đến Player. False: đánh hụt. Cả hai đi vào Timer attackRecovery → isAttacking=False để được đánh tiếp.' `
    @(3900,2180,6300,3000) @(0.36,0.17,0.08) @(
        @('39',3970,2380), @('43',3980,2660), @('41',4350,2380),
        @('74',4790,2340), @('31',4380,2810), @('100',5400,2380), @('51',5400,2680)
    )
Add-Section '08 | DỪNG TRONG LÚC HURT' `
    'Nhánh isHurt=True từ nhóm 04: vận tốc X=0, Animator isWalk=False. Chờ nhóm 11 đặt lại isHurt=False để tiếp tục hành vi.' `
    @(0,2180,1500,2780) @(0.28,0.12,0.30) @(
        @('134',180,2410), @('137',730,2410)
    )
Add-Section '09 | NHẬN ARROW VÀ LỌC TAG' `
    'On Trigger Enter 2D → lấy GameObject từ Collider → Compare Tag PlayerArrow → If đúng tag → If health > 0. Chỉ nhánh True chuyển sang nhóm 10.' `
    @(0,3200,1800,4100) @(0.34,0.13,0.17) @(
        @('141',70,3400), @('143',430,3670), @('104',770,3670),
        @('125',850,3400), @('146',1060,3930), @('150',1390,3670), @('160',1390,3400)
    )
Add-Section '10 | TRỪ MÁU VÀ RẼ NHÁNH' `
    'Hủy GameObject Arrow (T=0) → health = health − Integer 1 → kiểm tra Value vừa lưu > 0. True → nhóm 11 Hurt. False → nhóm 12 chết.' `
    @(2000,3200,3600,4100) @(0.36,0.11,0.13) @(
        @('154',2070,3400), @('164',2160,3910), @('162',2410,3670),
        @('166',2690,3400), @('168',2970,3670), @('176',3260,3400)
    )
Add-Section '11 | HURT VÀ HỒI PHỤC' `
    'Còn máu: Object isHurt=True → Animator Trigger gotHit → Timer 0.36 giây → isHurt=False. Nhóm 08 dừng chạy trong thời gian này.' `
    @(3800,3200,6300,4100) @(0.28,0.12,0.30) @(
        @('170',3870,3400), @('158',3900,3720), @('172',4340,3400),
        @('178',4790,3360), @('180',5400,3400), @('182',5420,3720)
    )
Add-Section '12 | CHẾT VÀ HỦY GOLEM' `
    'Hết máu: doDie → vận tốc (0,0) → Gravity=0 → tắt BoxCollider2D → Destroy This sau 0.85 giây → tắt ScriptMachine. Animator vẫn phát animation chết trong thời gian chờ.' `
    @(2000,4300,6300,5100) @(0.25,0.13,0.13) @(
        @('184',2070,4490), @('188',2630,4490), @('191',3190,4490),
        @('194',3750,4490), @('56',4310,4490), @('199',4320,4840), @('201',4890,4490)
    )

if ($assigned.Count -ne $nodes.Count) {
    $missing = @($nodes | Where-Object { -not $assigned.ContainsKey([string]$_.'$id') } | ForEach-Object { $_.'$id' })
    throw ('Nodes not assigned to a section: ' + ($missing -join ', '))
}
for ($i=0; $i -lt $groups.Count; $i++) {
    for ($j=$i+1; $j -lt $groups.Count; $j++) {
        $a=$groups[$i].position; $b=$groups[$j].position
        if ($a.xMin -lt $b.xMax -and $a.xMax -gt $b.xMin -and $a.yMin -lt $b.yMax -and $a.yMax -gt $b.yMin) {
            throw "Overlapping frames: $($groups[$i].label), $($groups[$j].label)"
        }
    }
}
$graph.elements = @($graph.elements) + @($groups.ToArray())
$graph.pan.x = 3150.0
$graph.pan.y = 2550.0
$graph.zoom = 0.12

# Full Serializer needs the original definition-before-reference order preserved.
$seen = New-Object 'System.Collections.Generic.HashSet[string]'
function Test-ReferenceOrder($value) {
    if ($null -eq $value -or $value -is [string] -or $value.GetType().IsValueType) { return }
    if ($value -is [System.Management.Automation.PSCustomObject]) {
        if ($value.PSObject.Properties['$id']) {
            if (-not $seen.Add([string]$value.'$id')) { throw ('Duplicate serialized ID: ' + $value.'$id') }
        }
        if ($value.PSObject.Properties['$ref'] -and -not $seen.Contains([string]$value.'$ref')) {
            throw ('Forward reference: ' + $value.'$ref')
        }
        foreach ($property in $value.PSObject.Properties) { Test-ReferenceOrder $property.Value }
    } elseif ($value -is [System.Collections.IEnumerable]) {
        foreach ($item in $value) { Test-ReferenceOrder $item }
    }
}
Test-ReferenceOrder $payload
$newJson = $payload | ConvertTo-Json -Depth 100 -Compress
$escaped = $newJson.Replace("'", "''")
$newRaw = $raw.Substring(0,$match.Groups[1].Index) + $escaped + $raw.Substring($match.Groups[1].Index+$match.Groups[1].Length)

# Reparse the exact file bytes-to-be-written; compare every original element.
$checkMatch = [regex]::Match($newRaw, "    _json: '([\s\S]*?)'\r?\n    _objectReferences:")
$check = ($checkMatch.Groups[1].Value.Replace("''", "'") | ConvertFrom-Json)
$checkElements = @($check.graph.elements | Where-Object { $_.'$type' -ne 'Unity.VisualScripting.GraphGroup' })
if ($checkElements.Count -ne $meaningBefore.Count) { throw 'Original element count changed.' }
for ($i=0; $i -lt $checkElements.Count; $i++) {
    $element=$checkElements[$i]
    if ([string]$element.guid -ne $orderBefore[$i]) { throw 'Serialized element order changed.' }
    if ((Get-ElementMeaning $element) -cne $meaningBefore[[string]$element.guid]) {
        throw ('Behavior changed for element ' + $element.guid)
    }
}
if ($newRaw.Substring(0,$match.Groups[1].Index) -cne $raw.Substring(0,$match.Groups[1].Index)) { throw 'Asset header changed.' }
if ((Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash -ne $originalHash) { throw 'Graph changed during layout preparation; retry from latest save.' }

$report = [ordered]@{
    nodeCount=$nodes.Count; connectionCount=$connections.Count; groupCount=$groups.Count
    behaviorPreserved=$true; serializedOrderPreserved=$true; referenceOrderValid=$true
    groupFramesDoNotOverlap=$true; allNodesAssignedExactlyOnce=$true
    sections=@($groups | ForEach-Object { [ordered]@{label=$_.label;description=$_.comment;position=$_.position} })
    nodeMembership=@($membership.ToArray())
}
if (-not $Apply) {
    [pscustomobject]$report | Select-Object nodeCount,connectionCount,groupCount,behaviorPreserved,serializedOrderPreserved,referenceOrderValid | ConvertTo-Json -Compress
    Write-Output 'DRY RUN PASSED; graph not changed.'
    return
}

$backup = Join-Path $root ('Backups\GolemGraphLayout\' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
[void][IO.Directory]::CreateDirectory($backup)
[IO.File]::Copy($asset,(Join-Path $backup 'GolemBlueCombat.before-layout.asset'))
[IO.File]::Copy(($asset+'.meta'),(Join-Path $backup 'GolemBlueCombat.asset.meta'))
[IO.File]::WriteAllText((Join-Path $backup 'verification.json'),($report | ConvertTo-Json -Depth 20),$utf8)
[IO.File]::WriteAllText($asset,$newRaw,$utf8)

$guide = @'
# Luồng hoạt động Golem Blue

Mở **Enemy → Golem_blue → Script Machine → Edit Graph** để xem `GolemBlueCombat`.
Graph được chia thành 12 khung màu có đánh số. Phóng to khung cần giải thích để đọc các node.
Chọn một khung để đọc phần **Comment** trong Graph Inspector.

| Khung | Chức năng | Nội dung cần trình bày |
|---|---|---|
| 01 | Khởi tạo | On Start đặt 7 máu và đặt isAttacking, isHurt bằng False. |
| 02 | Phát hiện Player | On Became Visible đặt isAwake bằng True. Camera Scene view cũng có thể kích hoạt sự kiện này trong Editor. |
| 03 | Hướng và khoảng cách | Tính Player X − Golem X; so sánh dấu để chọn hướng; dùng Abs và attackRange để kiểm tra tầm ngang. Đây là dữ liệu dùng chung. |
| 04 | Chọn hành vi | On Update kiểm tra isAwake, isHurt và tầm đánh để chọn nhánh. |
| 05 | Đuổi và quay mặt | Vận tốc X dương/âm, Flip X và Animator isWalk theo hướng Player. |
| 06 | Bắt đầu đòn đánh | Dừng chạy, kiểm tra isAttacking, khóa đòn mới, phát doAttack rồi bắt đầu Timer attackDelay. |
| 07 | Gây sát thương và nghỉ | Kiểm tra lại tầm; trúng thì gửi PlayerTakeDamage. Trúng hoặc hụt đều chờ attackRecovery rồi trả isAttacking về False. |
| 08 | Dừng trong lúc Hurt | isHurt đang True thì dừng vận tốc X và tắt isWalk. |
| 09 | Nhận Arrow và lọc tag | On Trigger Enter 2D lấy đối tượng vừa chạm, kiểm tra tag PlayerArrow và health > 0. |
| 10 | Trừ máu và rẽ nhánh | Hủy Arrow; trừ 1 máu; dùng giá trị vừa lưu để chọn Hurt hoặc Die. |
| 11 | Hurt và hồi phục | Đặt isHurt=True, phát gotHit, chờ 0.36 giây, đặt isHurt=False. |
| 12 | Chết và hủy Golem | Phát doDie, dừng vật lý, tắt collider, lên lịch hủy sau 0.85 giây, tắt Script Machine. |

## Ba luồng nên trình bày

```mermaid
flowchart TD
    START[01 · Bắt đầu game] --> INIT[7 máu; chưa đánh; chưa Hurt]
    VISIBLE[02 · Xuất hiện trong tầm nhìn] --> AWAKE[isAwake = True]
    UPDATE[04 · Mỗi khung hình] --> WAKE{Đã thức?}
    AWAKE -. Dữ liệu .-> WAKE
    WAKE -->|Có| HURT{Đang Hurt?}
    HURT -->|Có| STOP[08 · Dừng chạy]
    HURT -->|Không| RANGE{Trong tầm ngang?}
    DIST[03 · Tính hướng và khoảng cách] -. Dữ liệu .-> RANGE
    RANGE -->|Không| CHASE[05 · Đuổi và quay mặt]
    RANGE -->|Có| ATTACK[06 · Bắt đầu đòn nếu chưa đánh]
    ATTACK --> STRIKE[07 · Chờ ra đòn; kiểm tra lại tầm; gây sát thương nếu trúng]
    STRIKE --> RECOVER[Nghỉ rồi cho phép đòn tiếp theo]
    ARROW[09 · Arrow chạm Golem] --> HP[10 · Hủy Arrow và trừ 1 máu]
    HP --> LIVE{Máu mới lớn hơn 0?}
    LIVE -->|Có| HIT[11 · Hurt và hồi phục]
    LIVE -->|Không| DIE[12 · Die và hủy Golem]
```

**Flow trắng** cho biết thứ tự thực hiện. **Dây Data** truyền giá trị để các node tính toán và kiểm tra điều kiện.
Các biến health, Player, moveSpeed, attackRange, isAwake, isAttacking, isHurt thuộc **Object**.
isWalk, doAttack, gotHit, doDie thuộc **Animator Parameters**.

Những phần đã học thêm khi làm: Mathf Abs, đọc Transform.position và Vector3.x,
Set Linear Velocity X, Custom Event/Trigger Custom Event, và This.

Lần sắp xếp này chỉ thay đổi vị trí node, thêm khung và mô tả.
Mọi node hành vi, giá trị, dây Flow/Data, GUID và thứ tự tham chiếu được đối chiếu với bản sao trước khi sửa.
Các khung không tạo thêm hành vi; không cần chạy lại toàn bộ kiểm thử chiến đấu chỉ vì việc chia khung.
'@
[IO.File]::WriteAllText((Join-Path $root 'GolemBlue_LuongHoatDong.md'),$guide,$utf8)
Write-Output ('APPLIED: ' + $nodes.Count + ' nodes, ' + $connections.Count + ' wires, ' + $groups.Count + ' groups.')
Write-Output ('BACKUP: ' + $backup)
Write-Output 'CHECKED: behavior, values, wires, GUIDs, serialized order preserved; no C# created.'
