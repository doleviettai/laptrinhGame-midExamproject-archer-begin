# Skeleton combat - Visual Scripting

## Scope and stats
Skeleton first. Bee, blue Golem and yellow Golem keep their current setup.
Player Object Variables: PlayerHealth (Integer = 15), maxHealth (Integer = 15),
isDead (Boolean = false), PlayerControls (ScriptMachine = existing Player_flip machine).
Skeleton Object Variables: health (Integer = 3), moveSpeed (Float = 2.4),
attackRange (Float = 1.6), attackVerticalRange (Float = 1.75),
attackDelay (Float = 0.25), attackRecovery (Float = 0.6),
isAwake / isHurt / isAttacking (Boolean = false),
Player (GameObject = Player), MainCamera (GameObject = Player/Main Camera).
All health and transient state variables reset on Start.

## Components
Player adds a second Script Machine: PlayerHealth.
Skeleton adds Rigidbody2D (Dynamic, Gravity 3, Freeze Rotation Z);
BoxCollider2D (not Trigger, Size 1.1 x 2.55, Offset -0.2 / -0.1);
Variables and Script Machine: SkeletonCombat. Tag Enemy.
Arrow prefab retains its Trigger collider and PlayerArrow tag.

## SkeletonCombat graph
Select Enemy/Skeleton -> Script Machine -> Edit Graph.
Group 1: Object variable refs; Transform positions; BoxCollider2D Get Bounds ->
Bounds Get Center -> Vector3 Get X/Y -> Subtract -> Mathf Abs.
Compare distance X <= attackRange and Y <= attackVerticalRange with And.
Camera World To Viewport Point uses MainCamera, position = Skeleton world position.
Compare viewport X and Y between 0 and 1 and Z > 0; combine with And.
This checks the actual Game camera, so Scene view alone cannot wake the Skeleton.

On Start -> Set Object health = 3 -> Set Object isAwake = false ->
Set Object isHurt = false -> Set Object isAttacking = false.
All Set Variable input values are wired from typed Literals.

On Update -> If health > 0 -> If PlayerHealth > 0 ->
If isAwake. If false, check visibility and set isAwake true once visible.
If isHurt or isAttacking: set Rigidbody2D Linear Velocity X = 0, Animator isWalk false.
Otherwise, If in attack range: face Player -> stop -> isWalk false ->
isAttacking true -> Animator Set Trigger doAttack -> Timer attackDelay.
Outside range: Mathf Sign(deltaX) * moveSpeed -> Set Linear Velocity X;
deltaX < 0 -> SpriteRenderer Set Flip X; Animator isWalk true.

Timer Completed -> If alive, Player alive, still in range, and not hurt ->
Trigger Custom Event (Target Player, Name PlayerTakeDamage, Arguments 0).
Both valid-hit and missed-hit branches start Timer attackRecovery.
Recovery Completed -> Set Object isAttacking false.
One strike event per attack; moving away or jumping out of reach avoids damage.

On Trigger Enter 2D -> collider -> Component Get Game Object -> Compare Tag PlayerArrow ->
If true and health > 0 -> Object Destroy (other GameObject, t = 0) ->
Get Object health -> Subtract 1 -> Set Object health ->
If new health > 0:
isHurt true -> stop -> isWalk false -> Animator Trigger gotHit ->
Timer 0.36 -> isHurt false.
Else:
Animator Trigger doDie -> Rigidbody2D velocity (0,0), Gravity 0 ->
BoxCollider2D disabled -> Object Destroy Self after 0.95 sec.

## PlayerHealth graph
Select Player -> second Script Machine -> Edit Graph.
On Start -> Set Object PlayerHealth = 15 -> Set Object isDead = false.
Custom Event PlayerTakeDamage (Arguments 0) -> If PlayerHealth > 0 ->
Subtract 1 -> Set Object PlayerHealth -> If new HP > 0:
Animator Set Trigger isEatHit (Any State -> eat_hit; exit time returns to Idle).
Else: isDead true -> Animator Play Death -> velocity (0,0) ->
Gravity 0 -> BoxCollider2D disabled -> PlayerControls ScriptMachine disabled.
No UI/Game Over panel in this step.

## Animator
Skeleton parameters: isWalk Boolean; doAttack, gotHit, doDie Trigger.
Idle <-> skeleton_walking via isWalk.
Any State -> skeleton_dead (doDie), skeleton_eat_hit (gotHit), skeleton_attack1 (doAttack).
Attack / Hurt -> Idle use Exit Time 1, Duration 0. Attack/Hurt/Die clips do not loop.
Player isEatHit is Trigger, Any State -> eat_hit; Hurt -> Idle has Exit Time 1.
Player Death does not loop.

## Kien thuc bo sung
Custom Event and Trigger Custom Event connect enemy strikes to Player.
Camera WorldToViewportPoint checks the actual Game camera.
Mathf Abs/Sign, And/Negate, typed Literals, Set Linear Velocity X, Bounds and Get X/Y.
All nodes are built-in Visual Scripting units or Unity API members; no C# was created.

## Check in Play
Before entering the Game camera: Skeleton stays Idle.
Approach (jump over the one-tile step if needed): Skeleton wakes and runs to Player.
Stand in range: each completed strike reduces PlayerHealth by 1 and plays eat_hit.
Shoot J: Arrow disappears at the Skeleton, health goes 3 -> 2 -> 1 -> 0.
Skeleton plays Hurt on nonlethal hits, Die on the third; dead Skeleton cannot attack.
At PlayerHealth 0: Death plays and movement/shooting controls stop.
Stop and Play again: Player has 15 HP, Skeleton has 3 HP.
Read PlayerHealth / health in the corresponding GameObject Variables Inspector.
Skeleton chases horizontally over ground; no pathfinding or automatic jumping across pits.
