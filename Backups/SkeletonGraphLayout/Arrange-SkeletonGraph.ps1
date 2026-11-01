param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$root = 'D:\GamePrograms\MidTestExam'
$asset = Join-Path $root 'Assets\Script\SkeletonCombat.asset'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$raw = [IO.File]::ReadAllText($asset,$utf8)
$originalHash = (Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash
$match = [regex]::Match($raw,"    _json: '([\s\S]*?)'\r?\n    _objectReferences:")
if (-not $match.Success) { throw 'Cannot find embedded Skeleton graph JSON.' }
$json = ($match.Groups[1].Value -replace '\r?\n[ ]+',' ').Replace("''","'")
$payload = $json | ConvertFrom-Json
$graph = $payload.graph
$originalElements = @($graph.elements | Where-Object { $_.'$type' -ne 'Unity.VisualScripting.GraphGroup' })
$nodes = @($originalElements | Where-Object { $_.'$type' -notmatch 'Connection$' })
$connections = @($originalElements | Where-Object { $_.'$type' -match 'Connection$' })
$oldGroups = @($graph.elements | Where-Object { $_.'$type' -eq 'Unity.VisualScripting.GraphGroup' })
if (@($oldGroups | Where-Object { $_.label -eq '14 | CHẾT VÀ HỦY SKELETON' }).Count -gt 0) {
    throw 'Skeleton layout is already arranged; inspect before running again.'
}
function Get-ElementMeaning($element) {
    $meaning = [ordered]@{}
    foreach ($property in $element.PSObject.Properties) {
        if ($property.Name -ne 'position') { $meaning[$property.Name] = $property.Value }
    }
    return ($meaning | ConvertTo-Json -Depth 100 -Compress)
}
$meaningBefore = @{}
$nodesById = @{}
foreach ($element in $originalElements) { $meaningBefore[[string]$element.guid] = Get-ElementMeaning $element }
foreach ($node in $nodes) { $nodesById[[string]$node.'$id'] = $node }
$orderBefore = @($originalElements | ForEach-Object { [string]$_.guid })
if ($nodes.Count -ne 141 -or $connections.Count -ne 181) { throw 'Skeleton graph changed; inspect the new graph first.' }
if ($nodesById['9'].guid -ne 'c6d0fe41-ee56-4c8e-863a-1b0eab9d007b') { throw 'Shared This node changed.' }
if ($nodesById['29'].guid -ne '0d74e3e5-f6e9-4657-9e5a-a6aaf63ff402') { throw 'Arrow hit event changed.' }
if ($nodesById['308'].'$type' -ne 'Unity.VisualScripting.Start') { throw 'Start event changed.' }

$groups = New-Object 'System.Collections.Generic.List[object]'
$assigned = @{}
$membership = New-Object 'System.Collections.Generic.List[object]'
function Add-Section($label,$comment,$rect,$color,$placements) {
    foreach ($place in $placements) {
        $id = [string]$place[0]
        if (-not $nodesById.ContainsKey($id)) { throw "Unknown node $id in $label" }
        if ($assigned.ContainsKey($id)) { throw "Node $id assigned twice." }
        $node = $nodesById[$id]
        $node.position.x = [double]($rect[0]+$place[1])
        $node.position.y = [double]($rect[1]+$place[2])
        if ($node.position.x -lt $rect[0]+20 -or $node.position.x+280 -gt $rect[2] -or
            $node.position.y -lt $rect[1]+100 -or $node.position.y+130 -gt $rect[3]) {
            throw "Node $id outside the section $label"
        }
        $assigned[$id] = $label
        $membership.Add([pscustomobject]@{nodeGuid=$node.guid;nodeId=$id;section=$label})
    }
    $groups.Add([pscustomobject][ordered]@{
        position=[pscustomobject][ordered]@{
            xMin=[double]$rect[0];yMin=[double]$rect[1];xMax=[double]$rect[2];yMax=[double]$rect[3]
        }
        label=$label
        comment=$comment
        color=[pscustomobject][ordered]@{r=[double]$color[0];g=[double]$color[1];b=[double]$color[2];a=1.0}
        guid=[guid]::NewGuid().ToString()
        '$version'='A'
        '$type'='Unity.VisualScripting.GraphGroup'
    })
}

Add-Section '01 | KHỞI TẠO' `
    'On Start → health=3 → isAwake=False → isHurt=False → isAttacking=False. Đây là các biến Object riêng của Skeleton.' `
    @(0,0,2100,750) @(0.13,0.30,0.20) @(
        @('308',70,180),@('304',420,180),@('312',420,470),
        @('271',840,180),@('302',840,470),@('275',1260,180),@('273',1260,470),
        @('279',1680,180),@('277',1680,470)
    )
Add-Section '02 | THAM CHIẾU' `
    'This là GameObject Skeleton; Player và MainCamera lấy từ Object Variables. Các đầu ra này cấp Target cho nhiều nhóm khác, không phải luồng Flow.' `
    @(2300,0,3600,750) @(0.10,0.29,0.31) @(
        @('9',70,180),@('236',490,180),@('234',490,480)
    )
Add-Section '03 | TỌA ĐỘ NHÂN VẬT' `
    'Đọc BoxCollider2D.bounds.center của Player và Skeleton, rồi tách X/Y. Dùng tâm collider để khoảng cách tính theo cơ thể, không phụ thuộc khoảng trống trong sprite.' `
    @(3800,0,6300,750) @(0.10,0.23,0.36) @(
        @('253',70,180),@('256',620,180),@('219',1170,180),@('195',1720,180),
        @('265',70,500),@('222',620,500),@('216',1170,500),@('178',1720,500)
    )
Add-Section '04 | HƯỚNG VÀ TẦM ĐÁNH' `
    'Tính deltaX/deltaY giữa hai tâm collider. Abs(deltaX) ≤ attackRange và Abs(deltaY) ≤ attackVerticalRange → trong tầm. Sign(deltaX) × moveSpeed cho vận tốc đuổi; deltaX < 0 điều khiển Flip X.' `
    @(0,950,3600,1950) @(0.10,0.23,0.36) @(
        @('181',70,180),@('185',530,180),@('198',1010,180),@('193',1010,450),
        @('183',70,580),@('189',530,580),@('200',1010,580),@('214',1010,840),
        @('202',1510,450),@('204',2000,180),@('208',2000,450),@('210',2450,180),
        @('212',2000,840),@('259',2450,580)
    )
Add-Section '05 | CAMERA PHÁT HIỆN' `
    'WorldToViewportPoint dùng MainCamera và vị trí Skeleton. Kiểm tra 0 < X < 1, 0 < Y < 1, Z > 0. Nếu nhìn thấy → isAwake=True. Nhóm 06 gọi nhánh này khi Skeleton chưa thức; camera Scene view không quyết định điều kiện này.' `
    @(3800,950,7800,2250) @(0.10,0.29,0.31) @(
        @('250',70,180),@('261',500,180),
        @('295',970,180),@('268',970,530),@('338',970,880),
        @('310',1420,180),@('341',1420,410),@('316',1820,180),@('314',1820,410),
        @('318',1420,530),@('324',1420,760),@('322',1820,530),@('320',1820,760),
        @('328',1420,880),@('326',1420,1120),
        @('330',2280,180),@('332',2280,530),@('334',2280,880),@('336',2670,880),
        @('287',3060,530),@('291',3460,530),@('289',3460,820)
    )
Add-Section '06 | CHỌN HÀNH VI' `
    'On Update kiểm tra Skeleton còn máu, Player còn máu và isAwake. Chưa thức → nhóm 05. Đang Hurt/đang đánh hoặc Player hết máu → nhóm 07 dừng. Ngoài tầm → nhóm 08 đuổi; trong tầm → nhóm 09 bắt đầu đòn.' `
    @(0,2450,3900,3350) @(0.18,0.25,0.35) @(
        @('281',70,150),@('232',70,430),@('230',70,680),@('228',460,430),@('306',460,150),
        @('238',900,430),@('240',900,680),@('242',1310,430),@('283',1310,150),
        @('248',1750,430),@('285',1750,150),@('244',2220,430),@('293',2220,150),
        @('246',2670,430),@('300',2670,150),@('298',3180,150)
    )
Add-Section '07 | DỪNG TẠM THỜI' `
    'Các nhánh dừng từ nhóm 06/05 dùng chung: Set Linear Velocity X=0 → Animator isWalk=False. Nhóm này giữ vận tốc Y để trọng lực vẫn hoạt động.' `
    @(4100,2450,5900,3200) @(0.28,0.12,0.30) @(
        @('225',70,210),@('176',70,480),@('52',650,210),@('174',650,480),@('94',1100,480)
    )
Add-Section '08 | ĐUỔI PLAYER' `
    'Ngoài tầm đánh: Flip X theo dấu deltaX → Set Linear Velocity X = Sign(deltaX) × moveSpeed → Animator isWalk=True. Hướng và tốc độ được tính ở nhóm 04.' `
    @(6100,2450,7800,3200) @(0.10,0.31,0.22) @(
        @('56',70,210),@('59',500,210),@('66',960,210),@('62',960,480),@('64',1360,480)
    )
Add-Section '09 | BẮT ĐẦU ĐÒN ĐÁNH' `
    'Trong tầm: quay mặt về Player → dừng X → isWalk=False → isAttacking=True → Trigger doAttack → Timer attackDelay. isAttacking chặn việc bắt đầu đòn mới mỗi frame.' `
    @(0,3550,3900,4450) @(0.35,0.24,0.08) @(
        @('70',70,180),@('75',480,180),@('73',480,470),
        @('82',900,180),@('78',900,470),@('80',900,740),
        @('88',1350,180),@('86',1350,470),@('48',1800,180),@('90',1800,470),
        @('44',2340,130),@('46',2340,740)
    )
Add-Section '10 | ĐÒN TRÚNG VÀ NGHỈ' `
    'Timer ra đòn Completed → kiểm tra Skeleton còn sống, Player còn sống, vẫn trong tầm và Skeleton không Hurt. Đúng → gửi PlayerTakeDamage. Trúng/hụt đều qua Timer attackRecovery → isAttacking=False.' `
    @(4100,3450,7800,4450) @(0.36,0.17,0.08) @(
        @('11',70,180),@('13',460,180),@('23',460,480),@('15',850,180),
        @('17',1280,180),@('19',1700,180),@('25',2180,130),@('21',2180,740),
        @('27',2760,180),@('42',2760,480)
    )
Add-Section '11 | NHẬN ARROW' `
    'On Trigger Enter 2D → lấy GameObject từ collider → Compare Tag PlayerArrow → If đúng tag → If health > 0. Chỉ Skeleton còn sống mới xử lý tên trúng.' `
    @(0,4650,2100,5650) @(0.34,0.13,0.17) @(
        @('29',70,180),@('31',400,500),@('34',1000,840),
        @('36',1000,500),@('40',1000,180),@('92',1510,180)
    )
Add-Section '12 | TRỪ MÁU' `
    'Hủy GameObject Arrow ngay (T=0) → health = health − Integer 1 → kiểm tra Value vừa lưu > 0. True → nhóm 13 Hurt. False → nhóm 14 chết.' `
    @(2300,4650,4400,5650) @(0.36,0.11,0.13) @(
        @('170',70,180),@('96',70,500),@('135',550,500),@('98',350,840),
        @('137',900,180),@('139',1330,840),@('141',1330,500),@('143',1600,180)
    )
Add-Section '13 | HURT VÀ HỒI PHỤC' `
    'Còn máu: isHurt=True → dừng X → isWalk=False → Trigger gotHit → Timer 0.36 giây → isHurt=False. Sau đó nhóm 06 cho phép tiếp tục đuổi/đánh.' `
    @(4600,4650,7800,5650) @(0.28,0.12,0.30) @(
        @('147',70,180),@('145',70,500),@('151',490,180),@('149',490,500),
        @('158',910,180),@('154',910,500),@('156',910,840),
        @('164',1380,180),@('162',1380,500),@('133',1880,130),@('168',1880,840),
        @('129',2460,180),@('131',2460,500)
    )
Add-Section '14 | CHẾT VÀ HỦY SKELETON' `
    'Hết máu: Trigger doDie → vận tốc (0,0) → Gravity=0 → tắt BoxCollider2D → Destroy This sau 0.95 giây. Điều kiện health > 0 trong nhóm 06/10 ngăn chạy và gây sát thương khi đã chết.' `
    @(2300,5850,7800,6600) @(0.25,0.13,0.13) @(
        @('100',70,180),@('118',70,500),@('108',870,180),@('104',870,500),
        @('113',1670,180),@('111',1670,500),@('120',2470,180),@('116',2470,500),
        @('123',3270,180),@('127',3270,500)
    )

if ($assigned.Count -ne $nodes.Count) {
    $missing=@($nodes | Where-Object {-not $assigned.ContainsKey([string]$_.'$id')} | ForEach-Object {$_.'$id'})
    throw ('Nodes not assigned: '+($missing -join ', '))
}
for ($i=0;$i -lt $groups.Count;$i++) {
    for ($j=$i+1;$j -lt $groups.Count;$j++) {
        $a=$groups[$i].position;$b=$groups[$j].position
        if ($a.xMin -lt $b.xMax -and $a.xMax -gt $b.xMin -and $a.yMin -lt $b.yMax -and $a.yMax -gt $b.yMin) {
            throw "Overlapping frames: $($groups[$i].label), $($groups[$j].label)"
        }
    }
}
$graph.elements=@($originalElements)+@($groups.ToArray())
$graph.pan.x=3900.0
$graph.pan.y=3300.0
$graph.zoom=0.1

# Traverse the complete serialization in its original order, including nested nodes.
$seen=New-Object 'System.Collections.Generic.HashSet[string]'
function Test-ReferenceOrder($value) {
    if ($null -eq $value -or $value -is [string] -or $value.GetType().IsValueType) {return}
    if ($value -is [System.Management.Automation.PSCustomObject]) {
        if ($value.PSObject.Properties['$id']) {
            if (-not $seen.Add([string]$value.'$id')) {throw ('Duplicate ID: '+$value.'$id')}
        }
        if ($value.PSObject.Properties['$ref'] -and -not $seen.Contains([string]$value.'$ref')) {
            throw ('Forward reference: '+$value.'$ref')
        }
        foreach ($property in $value.PSObject.Properties) {Test-ReferenceOrder $property.Value}
    } elseif ($value -is [System.Collections.IEnumerable]) {
        foreach ($item in $value) {Test-ReferenceOrder $item}
    }
}
Test-ReferenceOrder $payload
$newJson=$payload | ConvertTo-Json -Depth 100 -Compress
$escaped=$newJson.Replace("'","''")
$newRaw=$raw.Substring(0,$match.Groups[1].Index)+$escaped+$raw.Substring($match.Groups[1].Index+$match.Groups[1].Length)
$checkMatch=[regex]::Match($newRaw,"    _json: '([\s\S]*?)'\r?\n    _objectReferences:")
$check=$checkMatch.Groups[1].Value.Replace("''","'") | ConvertFrom-Json
$checkElements=@($check.graph.elements | Where-Object {$_.'$type' -ne 'Unity.VisualScripting.GraphGroup'})
if ($checkElements.Count -ne $originalElements.Count) {throw 'Original element count changed.'}
for ($i=0;$i -lt $checkElements.Count;$i++) {
    $element=$checkElements[$i]
    if ([string]$element.guid -ne $orderBefore[$i]) {throw 'Serialized element order changed.'}
    if ((Get-ElementMeaning $element) -cne $meaningBefore[[string]$element.guid]) {
        throw ('Behavior changed for element '+$element.guid)
    }
}
if ((Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash -ne $originalHash) {
    throw 'Graph changed during preparation; read the latest save first.'
}
$report=[ordered]@{
    nodeCount=$nodes.Count;connectionCount=$connections.Count;previousGroupCount=$oldGroups.Count;newGroupCount=$groups.Count
    behaviorPreserved=$true;serializedOrderPreserved=$true;referenceOrderValid=$true
    framesDoNotOverlap=$true;eachNodeAssignedOnce=$true
    sections=@($groups | ForEach-Object {[ordered]@{label=$_.label;description=$_.comment;position=$_.position}})
    nodeMembership=@($membership.ToArray())
}
if (-not $Apply) {
    [pscustomobject]$report | Select-Object nodeCount,connectionCount,previousGroupCount,newGroupCount,behaviorPreserved,serializedOrderPreserved,referenceOrderValid | ConvertTo-Json -Compress
    Write-Output 'DRY RUN PASSED; Skeleton graph not changed.'
    return
}
$backup=Join-Path $root ('Backups\SkeletonGraphLayout\'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
[void][IO.Directory]::CreateDirectory($backup)
[IO.File]::Copy($asset,(Join-Path $backup 'SkeletonCombat.before-layout.asset'))
[IO.File]::Copy(($asset+'.meta'),(Join-Path $backup 'SkeletonCombat.asset.meta'))
[IO.File]::WriteAllText((Join-Path $backup 'verification.json'),($report | ConvertTo-Json -Depth 20),$utf8)
[IO.File]::WriteAllText($asset,$newRaw,$utf8)
Write-Output ('APPLIED: '+$nodes.Count+' nodes, '+$connections.Count+' wires, '+$groups.Count+' frames.')
Write-Output ('BACKUP: '+$backup)
Write-Output 'CHECKED: all original node values, wires, IDs, GUIDs, and reference order preserved.'
