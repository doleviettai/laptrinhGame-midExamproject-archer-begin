param([switch]$Apply)

$ErrorActionPreference='Stop'
$root='D:\GamePrograms\MidTestExam'
$asset=Join-Path $root 'Assets\Script\SkeletonCombat.asset'
$guidePath=Join-Path $root 'Skeleton_LuongHoatDong.md'
$utf8=New-Object System.Text.UTF8Encoding($false)
$raw=[IO.File]::ReadAllText($asset,$utf8)
$originalHash=(Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash
$m=[regex]::Match($raw,"    _json: '([\s\S]*?)'\r?\n    _objectReferences:")
if(-not $m.Success){throw 'Missing graph JSON'}
$payload=(($m.Groups[1].Value -replace '\r?\n[ ]+',' ').Replace("''","'") | ConvertFrom-Json)
$graph=$payload.graph
$originalElements=@($graph.elements)
$nodes=@($originalElements | Where-Object {$_.'$type' -notmatch 'Connection$|GraphGroup$'})
$groups=@($originalElements | Where-Object {$_.'$type' -eq 'Unity.VisualScripting.GraphGroup'})
$wires=@($originalElements | Where-Object {$_.'$type' -match 'Connection$'})
$selfNodes=@($nodes | Where-Object {$_.'$type' -eq 'Unity.VisualScripting.This'})
if($selfNodes.Count -ne 1){throw 'Expected one shared This; inspect the latest graph before changing it.'}
if($groups.Count -ne 14){throw 'Expected the 14 numbered Skeleton frames.'}
$shared=$selfNodes[0]
$sharedId=[string]$shared.'$id'
$byId=@{}
foreach($node in $nodes){$byId[[string]$node.'$id']=$node}
function Get-Frame($node){
    $result=@($groups | Where-Object {
        $node.position.x -ge $_.position.xMin -and $node.position.x -lt $_.position.xMax -and
        $node.position.y -ge $_.position.yMin -and $node.position.y -lt $_.position.yMax
    })
    if($result.Count -ne 1){throw ('Node does not belong to exactly one frame: '+$node.guid)}
    return $result[0]
}
function Element-Meaning($element){
    $record=[ordered]@{}
    foreach($property in $element.PSObject.Properties){
        if($property.Name -ne 'position'){$record[$property.Name]=$property.Value}
    }
    return ($record | ConvertTo-Json -Depth 100 -Compress)
}
$originalByGuid=@{}
foreach($element in $originalElements){
    $originalByGuid[[string]$element.guid]=($element | ConvertTo-Json -Depth 100 -Compress | ConvertFrom-Json)
}
$selfWires=@($wires | Where-Object {
    $_.'$type' -eq 'Unity.VisualScripting.ValueConnection' -and [string]$_.sourceUnit.'$ref' -eq $sharedId
})
if($selfWires.Count -ne 19){throw 'Shared This connections changed; inspect them first.'}
$framesNeedingThis=@{}
foreach($wire in $selfWires){
    if($wire.sourceKey -ne 'self'){throw 'Unexpected This output port'}
    $destination=$byId[[string]$wire.destinationUnit.'$ref']
    $frame=Get-Frame $destination
    $framesNeedingThis[[string]$frame.label.Substring(0,2)]=$frame
}
if($framesNeedingThis.Count -ne 7){throw 'Expected This targets in seven frames.'}

# Existing unused space in each frame keeps the additional sources away from other nodes.
$locations=@{
    '03'=@(3870,520)
    '05'=@(3870,1460)
    '07'=@(4500,3060)
    '08'=@(6380,2960)
    '09'=@(1400,4290)
    '13'=@(5050,5470)
    '14'=@(3900,6630)
}
# Make room to the left of Skeleton's own bounds row in the coordinates frame.
foreach($id in @('265','222','216','178')){
    if(-not $byId.ContainsKey($id)){throw 'Coordinate node IDs changed.'}
    $byId[$id].position.x=[double]($byId[$id].position.x+290)
}
$deathFrame=$framesNeedingThis['14']
$deathFrame.position.yMax=6820.0
$nextId=([int](@($nodes | ForEach-Object {[int]$_.'$id'}) | Measure-Object -Maximum).Maximum)+10
$newNodes=New-Object 'System.Collections.Generic.List[object]'
$thisByFrame=@{}
foreach($number in @('03','05','07','08','09','13','14')){
    if(-not $framesNeedingThis.ContainsKey($number)){throw ('Missing target frame '+$number)}
    if($number -eq '03'){
        $localThis=$shared
    }else{
        $localThis=($shared | ConvertTo-Json -Depth 100 -Compress | ConvertFrom-Json)
        $localThis.'$id'=[string]$nextId
        $nextId++
        $localThis.guid=[guid]::NewGuid().ToString()
        $newNodes.Add($localThis)
    }
    $localThis.position.x=[double]$locations[$number][0]
    $localThis.position.y=[double]$locations[$number][1]
    $thisByFrame[$number]=$localThis
    $frame=$framesNeedingThis[$number]
    $frame.comment += ' This trong khung chỉ tham chiếu GameObject Skeleton và cấp Target cho các node cùng khung.'
}
$referenceFrame=@($groups | Where-Object {$_.label -like '02 |*'})[0]
$referenceFrame.comment='Player và MainCamera lấy từ Object Variables, cấp tham chiếu đúng đối tượng cho các nhóm khác. Mỗi khung cần chính Skeleton có một node This riêng; không còn This dùng chung giữa các khung.'

$changedWireGuids=New-Object 'System.Collections.Generic.HashSet[string]'
foreach($wire in $selfWires){
    $frame=Get-Frame $byId[[string]$wire.destinationUnit.'$ref']
    $number=$frame.label.Substring(0,2)
    $wire.sourceUnit.'$ref'=[string]$thisByFrame[$number].'$id'
    [void]$changedWireGuids.Add([string]$wire.guid)
}
# Put added definitions before all existing references. The original elements keep their order.
$graph.elements=@($newNodes.ToArray())+@($originalElements)
$graph.pan.y=3410.0

# Original node semantics and all wire destinations must be identical.
foreach($element in $originalElements){
    $prior=$originalByGuid[[string]$element.guid]
    if($element.'$type' -eq 'Unity.VisualScripting.GraphGroup'){
        if($prior.guid -ne $element.guid -or $prior.label -cne $element.label -or
           ($prior.color | ConvertTo-Json -Compress) -cne ($element.color | ConvertTo-Json -Compress)){
            throw 'Frame identity, label or color changed.'
        }
    }elseif($changedWireGuids.Contains([string]$element.guid)){
        $copy=($element | ConvertTo-Json -Depth 100 -Compress | ConvertFrom-Json)
        $copy.sourceUnit.'$ref'=$sharedId
        if((Element-Meaning $copy) -cne (Element-Meaning $prior)){throw 'A This wire changed beyond its source.'}
        $source=@($thisByFrame.Values | Where-Object {[string]$_.'$id' -eq [string]$element.sourceUnit.'$ref'})
        if($source.Count -ne 1 -or $source[0].'$type' -ne 'Unity.VisualScripting.This'){throw 'Changed source is not This.'}
        if((Get-Frame $source[0]).guid -ne (Get-Frame $byId[[string]$element.destinationUnit.'$ref']).guid){throw 'This still crosses a frame boundary.'}
    }else{
        if((Element-Meaning $element) -cne (Element-Meaning $prior)){throw ('Node or wire behavior changed: '+$element.guid)}
    }
}
$seen=New-Object 'System.Collections.Generic.HashSet[string]'
function Test-References($value){
    if($null -eq $value -or $value -is [string] -or $value.GetType().IsValueType){return}
    if($value -is [System.Management.Automation.PSCustomObject]){
        if($value.PSObject.Properties['$id']){
            if(-not $seen.Add([string]$value.'$id')){throw ('Duplicate ID '+$value.'$id')}
        }
        if($value.PSObject.Properties['$ref'] -and -not $seen.Contains([string]$value.'$ref')){throw ('Forward reference '+$value.'$ref')}
        foreach($property in $value.PSObject.Properties){Test-References $property.Value}
    }elseif($value -is [System.Collections.IEnumerable]){
        foreach($item in $value){Test-References $item}
    }
}
Test-References $payload
foreach($number in $locations.Keys){
    $frame=$framesNeedingThis[$number]
    $inFrame=@($graph.elements | Where-Object {$_.'$type' -eq 'Unity.VisualScripting.This' -and (Get-Frame $_).guid -eq $frame.guid})
    if($inFrame.Count -ne 1){throw ('Expected exactly one This in '+$number)}
}
$newJson=$payload | ConvertTo-Json -Depth 100 -Compress
$escaped=$newJson.Replace("'","''")
$newRaw=$raw.Substring(0,$m.Groups[1].Index)+$escaped+$raw.Substring($m.Groups[1].Index+$m.Groups[1].Length)
$checkMatch=[regex]::Match($newRaw,"    _json: '([\s\S]*?)'\r?\n    _objectReferences:")
$check=($checkMatch.Groups[1].Value.Replace("''","'") | ConvertFrom-Json)
if(($check | ConvertTo-Json -Depth 100 -Compress) -cne $newJson){throw 'Reparse mismatch'}
if((Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash -ne $originalHash){throw 'Graph changed during editing; read latest save first.'}
$report=[ordered]@{
    beforeNodes=$nodes.Count;afterNodes=$nodes.Count+$newNodes.Count;wires=$wires.Count
    beforeThis=$selfNodes.Count;afterThis=$thisByFrame.Count;frames=$groups.Count
    rewiredThisConnections=$selfWires.Count;crossFrameThisConnections=0
    sameSelfTargetVerified=$true;allOtherBehaviorPreserved=$true;referenceOrderValid=$true
    sections=@($locations.Keys | Sort-Object | ForEach-Object {
        [ordered]@{label=$framesNeedingThis[$_].label;thisNodeId=$thisByFrame[$_].'$id';thisNodeGuid=$thisByFrame[$_].guid}
    })
}
if(-not $Apply){
    [pscustomobject]$report | Select-Object beforeNodes,afterNodes,wires,beforeThis,afterThis,rewiredThisConnections,crossFrameThisConnections,sameSelfTargetVerified,referenceOrderValid | ConvertTo-Json -Compress
    Write-Output 'DRY RUN PASSED; graph not changed.'
    return
}
$backup=Join-Path $root ('Backups\SkeletonGraphLayout\LocalThis_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
[void][IO.Directory]::CreateDirectory($backup)
[IO.File]::Copy($asset,(Join-Path $backup 'SkeletonCombat.before-local-this.asset'))
[IO.File]::Copy(($asset+'.meta'),(Join-Path $backup 'SkeletonCombat.asset.meta'))
[IO.File]::Copy($guidePath,(Join-Path $backup 'Skeleton_LuongHoatDong.before.md'))
[IO.File]::WriteAllText((Join-Path $backup 'verification.json'),($report | ConvertTo-Json -Depth 12),$utf8)
[IO.File]::WriteAllText($asset,$newRaw,$utf8)
$guide=[IO.File]::ReadAllText($guidePath,$utf8)
$guide=$guide.Replace('This là Skeleton; Player và MainCamera lấy từ Object Variables. Các node khác dùng chúng làm Target.','Player và MainCamera lấy từ Object Variables. Mỗi khung cần tham chiếu chính Skeleton có một node This riêng; dây Target của This nằm trong khung đó.')
$guide=$guide.Replace('Các phần kiến thức bổ sung đã dùng:', '**Tham chiếu This trong từng khung:** khung 03, 05, 07, 08, 09, 13 và 14 có mỗi khung một This. Các This đều trả về cùng GameObject Skeleton, không tạo bản sao Skeleton. Khung 02 giữ Player và MainCamera. Những node khác đã để Target mặc định This vẫn hoạt động như trước.'+[Environment]::NewLine+[Environment]::NewLine+'Các phần kiến thức bổ sung đã dùng:')
$guide=$guide.Replace('Lần sắp xếp này thay vị trí node, khung nhóm, mô tả và góc nhìn graph. Toàn bộ **141 node, 181 dây nối**, giá trị và thứ tự tham chiếu được giữ nguyên và đối chiếu với bản sao lưu trong `Backups/SkeletonGraphLayout`.','Graph hiện có **147 node và 181 dây nối**. Sáu node This được thêm để mỗi khung cần dùng có một nguồn Target riêng; 19 dây được đổi sang This cùng khung. Các giá trị, luồng Flow và đối tượng Target thực tế được giữ nguyên. Bản sao trước mỗi lần chỉnh nằm trong `Backups/SkeletonGraphLayout`.')
[IO.File]::WriteAllText($guidePath,$guide,$utf8)
Write-Output 'APPLIED: 7 This nodes across 7 frames; 19 This wires stay inside their destination frame.'
Write-Output ('BACKUP: '+$backup)
Write-Output 'Preserved: 181 wires, all Flow paths, all original values, Player/MainCamera targets, Skeleton self semantics.'
