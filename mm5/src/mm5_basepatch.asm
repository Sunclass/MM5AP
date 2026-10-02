norom
!headersize = 16

!controller_flip = $14 ; only on first frame of input, used by crash man, etc
!controller_mirror = $16
!vram_toggle = $19
!mega_man_state = $30
!current_weapon = $32
!current_stage = $6C
!completed_rbm_stages = $A9
!completed_proto_man_stages = $6F
; !deathlink = $30, set to $0E
!bank_1_read = $F3
!bank_2_read = $F4
!bank_1_write = $F5
!bank_2_write = $F6
!vram_buffer = $0780
!received_items = $6000
!received_rbm_stages = $6001
!received_cossack_stages = $6002
!current_proto_wily = $6003
!rbm_strobe = $6004
!sound_effect_strobe = $6005
!returning_latch = $6006
!energylink_health = $6007
!energylink_weapon = $6008
!energylink_lives = $6009
!bank_store = $600A
!received_charge_buster = $600B

!sent_items = $6064 ; this one is done really weird frankly, but this has it hit at $60B0, which is the actual weapons array
!sent_weapons = $60B0 ; this is equivalent to the above, but only used by weapons and not wire/balloon
!sent_beat = $60BB

!CONTROLLER_START = #$10
!CONTROLLER_SELECT = #$20
!CONTROLLER_SELECT_START = #$30
!CONTROLLER_ALL_BUTTON = #$F0

!PpuControl_2000 = $2000
!PpuMask_2001 = $2001
!PpuStatus_2002 = $2002
!PpuAddr_2006 = $2006
!PpuData_2007 = $2007

macro org(address,bank)
    if <bank> == $1E
        org <address>-$C000+($2000*<bank>)+!headersize ; org sets the position in the output file to write to (in norom, at least)
        base <address> ; base sets the position that all labels are relative to - this is necessary so labels will still start from $8000, instead of $0000 or somewhere
    else 
      if <bank> == $1F
          org <address>-$E000+($2000*<bank>)+!headersize ; org sets the position in the output file to write to (in norom, at least)
          base <address> ; base sets the position that all labels are relative to - this is necessary so labels will still start from $8000, instead of $0000 or somewhere
      else
        if <address> >= $A000
          org <address>-$A000+($2000*<bank>)+!headersize
          base <address>
        else
          org <address>-$8000+($2000*<bank>)+!headersize
          base <address>
        endif
      endif
    endif
endmacro

org 6
; We need to edit the NES 2.0 header here too
db $40, $08, $00, $00, $07, $07, $00, $00, $00, $01

;%org($80C0, $01)
    ;JMP     WeaponSoftlock
    ;NOP
    ;NOP
    ;NOP
    ;NOP
   
;%org($8C60, $01)
;WeaponSoftlock:
    ;ADC     $858A,Y
    ;STA     $50
    ;LDX     $50
    ;PHA
    ;TYA 
    ;PHA
    ;ORA     #$05
    ;TAY
    ;DEX
    ;DEX
    ;DEY
    ;.Loop
    ;LDY     $8594, X
    ;LDA     $B0, X
    ;BNE     .ContinueTrue
    ;DEX
    ;DEY
    ;CPY     #$05
    ;BNE     .Loop
    ; we're in the false case, jump out to a safe spot
    ;LDA     #$00
    ;STA     $0138
    ;PLA
    ;TAY
    ;PLA
    ;JMP     $80E1
;.ContinueTrue:
    ; true case, pull and return
    ;PLA
    ;TAY
    ;PLA
    ;JMP     $80D1

%org($8080, $0B)
    JMP     Wily3Requirement
    NOP

%org($83B0, $0B)
Wily3Requirement:
    LDY     #$00
    LDA     $6B
    .Loop:
    PHA
    AND     #$01
    BEQ     .Skip
    INY
    .Skip:
    PLA
    LSR
    CMP     #$00
    BNE     .Loop
    .Check:
    print   "Wily 3 Requirement: ", hex(realbase())
    CPY     #$03
    BMI     .False
    LDY     #$01
    LDA     #$FF
    BNE     .Return
    .False:
    LDA     #$00
    .Return:
    CMP     #$FF
    JMP     $8084

;Two orgs bundled together for StageSelectLoopHook

%org($8142, $17)
    AND     #$B0
%org($8146, $17)
    JMP     StageSelectLoopHook

%org($81D7, $17)
    JMP     CheckStageAccess
    NOP
    NOP
    NOP
    NOP

%org($81E2, $17)
    JMP     CheckProtoWily
    NOP

%org($92B6, $17)
    JMP     RemapProtoStage
    NOP

%org($81ED, $17)
    JMP     DrawCastle

%org($8864, $17)
    JMP     ReturnToStageSelect
    NOP

%org($886A, $17)
    JMP     ReturnCossackToStageSelect
    NOP
    NOP
    NOP

%org($8A9F, $17)
    JMP     InvertRBMSprites
    NOP

%org($89E7, $17)
    JMP     RemapWeaponReceive
    NOP

%org($89F0, $17)
    JMP     RemapRushReceive
    NOP


%org($9148, $1B)
    JMP     JammedBuster


%org($8BA8, $1B)
    JMP     MarkComplete
    NOP


%org($9C90, $17)
; InvertRBMSprites Org
InvertRBMSprites:
    LDA     !received_rbm_stages
    EOR     #$FF
    STA     $00
    JMP     $8AA3

; RemapWeaponReceive Org
RemapWeaponReceive:
    LDA     #$01
    STA     !sent_weapons, X
    JMP     $89EB

; RemapRushReceive Org
RemapRushReceive:
    LDA     #$01
    STA     !sent_weapons, X
    JMP     $89F4

; StageSelectLoopHook Org
StageSelectLoopHook:
    LDA     !controller_flip
    AND     #$90
    BEQ     .continue
    JMP     $81CD
    .continue:
    LDA     !controller_flip
    AND     !CONTROLLER_SELECT
    BEQ     .SoundEffects
    LDA     !current_proto_wily
    CLC
    ADC     #$01
    CMP     #$08
    BNE     .SetCurrent
    LDA     #$00
    .SetCurrent:
    STA     !current_proto_wily
    LDA     #$2D
    STA     !sound_effect_strobe
    LDY     #$00
    LDA     #$22
    STA     !vram_buffer, Y
    INY
    LDA     #$2F
    STA     !vram_buffer, Y
    INY
    LDA     #$01
    STA     !vram_buffer, Y
    INY
    LDA     !current_proto_wily
    CMP     #$04
    BMI     .Cossack
    LDA     #$57
    JMP     .SetDisplay
    .Cossack:
    LDA     #$50
    .SetDisplay:
    STA     !vram_buffer, Y
    INY
    LDA     !current_proto_wily
    CMP     #$04
    BMI     .SetValue
    SEC
    SBC     #$04
    .SetValue:
    CLC
    ADC     #$31
    STA     !vram_buffer, Y
    INY
    LDA     #$FF
    STA     !vram_buffer, Y
    LDA     #$01
    STA     !vram_toggle
    .SoundEffects:
    LDA     !sound_effect_strobe
    BEQ     .RbmStrobe
    JSR     $EC5B
    LDA     #$00
    STA     !sound_effect_strobe
    .RbmStrobe:
    JSR     $865A
    LDA     !rbm_strobe
    BEQ     .Return
    LDA     #$97
    STA     $0200
    LDA     #$00
    STA     !rbm_strobe
    LDA     #$00
    STA     $10 
    LDA     #$02
    STA     $23
    JSR     $DAFC
    BEQ     .Return
    .Return:
    JMP     $8149

; CheckStageAccess Org
CheckStageAccess:
    LDA     $8DA4, Y
    STA     $26
    STA     $6C
    CMP     #$08
    BPL     .ReturnSkip
    BEQ     .ReturnSkip
    PHA
    TAX
    LDA     #$01
    .Loop:
    CPX     #$00
    BEQ     .Continue
    ASL
    DEX
    CLC
    BCC     .Loop
    .Continue:
    AND     !received_rbm_stages
    CMP     #$00
    BNE     .ReturnSkipWithPull
    PLA
    JMP     $81C2 ;Stage is Locked
    .ReturnSkipWithPull:
    PLA
    .ReturnSkip:
    JMP     $81DE ;Stage is Unlocked


; CheckProtoWily Org
CheckProtoWily:
    LDA     !current_proto_wily
    CMP     #$04
    BEQ     .Wily1
    BMI     .Cossack
    ; we are trying to access wily 2/3/4, just check their previous flag
    TAX     
    DEX
    LDA     #$01
    .WilyLoop:
    CPX     #$00
    BEQ     .WilyContinue
    ASL
    DEX
    CLC
    BCC     .WilyLoop
    .WilyContinue:
    BIT     !completed_proto_man_stages
    BEQ     .ReturnFalse
    BNE     .ReturnTrue
    .Wily1:
    LDA     !completed_proto_man_stages
    AND     #$0F
    CMP     #$0F
    BEQ     .ReturnTrue
    BNE     .ReturnFalse
    .Cossack:
    TAX
    LDA     #$01
    .CossackLoop:
    CPX     #$00
    BEQ     .CossackContinue
    ASL
    DEX
    CLC
    BCC     .CossackLoop
    .CossackContinue:
    BIT     !received_cossack_stages
    BNE     .ReturnTrue
    BEQ     .ReturnFalse
    .ReturnTrue:
    LDA     #$FF
    BNE     .Return
    .ReturnFalse:
    LDA     #$2D
    STA     !sound_effect_strobe
    LDA     #$00
    .Return:
    CMP     #$FF
    JMP     $81E6

RemapProtoStage:
    LDX     !current_proto_wily
    LDA     #$01
    .Loop:
    CPX     #$00
    BEQ     .Continue
    ASL
    CLC
    ADC     #$01
    DEX
    CLC
    BCC     .Loop
    .Continue:
    LSR
    JMP     $92BA

DrawCastle:
    PHA
    LDA     !current_proto_wily
    CMP     #$04
    BMI     .ReturnWily
    PLA
    ;ReturnProto
    JMP     $92CD
    .ReturnWily:
    PLA
    JMP     $9272

ReturnToStageSelect:
    LDA     !returning_latch
    BEQ     .ReturnNormal
    LDA     #$00
    STA     !returning_latch
    JMP     $80E1
    .ReturnNormal:
    LDA     !current_stage
    CMP     #$08
    JMP     $8868

ReturnCossackToStageSelect:
    LDA     !current_stage
    CMP     #$0C
    BCS     .ReturnTrue
    JMP     $80E1
    .ReturnTrue:
    LDA     !current_proto_wily
    CLC
    ADC     #$01
    STA     !current_proto_wily
    LDA     !completed_proto_man_stages
    CMP     #$0F
    JMP     $8870

 

%org($9E70, $1B)
; Jammed Buster Org
JammedBuster:
    print   "Jammed Buster: ", hex(realbase())
    LDA     #$00
    BEQ     .Inc
    LDA     !received_charge_buster
    BEQ     .Return
    .Inc:
    INC     $38
    .Return:
    LDA     $38
    JMP     $914C

MarkComplete:
    LDA     #$80
    ORA     !completed_proto_man_stages
    STA     !completed_proto_man_stages
    LDA     $0528
    ORA     #$20
    STA     $0528
    JMP     $8BB0

%org($ADF6, $1D)
    CMP     #$89
    db $90, $03


%org($DE93, $1E)
    JMP     MegaManInputHook
    NOP

%org($F540, $1F)
MegaManInputHook:
    LDA     !controller_mirror
    AND     !CONTROLLER_ALL_BUTTON
    CMP     !CONTROLLER_ALL_BUTTON
    BNE     .SoundEffects
    LDA     #$10
    STA     !mega_man_state
    LDA     #$01
    STA     !returning_latch
    JMP     $DEAC
    .SoundEffects:
    LDA     !sound_effect_strobe
    BEQ     .Return
    JSR     $EC5B
    LDA     #$00
    STA     !sound_effect_strobe
    .Return:
    LDA     !controller_flip
    AND     !CONTROLLER_START
    JMP     $DE97

%org($AECE, $1D)
    JMP     EnergylinkOneUp
    NOP

%org($AED8, $1D)
    JMP     EnergylinkHealth
    NOP

%org($AEDC, $1D)
    JMP     EnergylinkEnergy
    NOP

%org($AA80, $1D)
EnergylinkEnergy:
    ; called if you pick up weapon Energy
    print "Energylink: ", hex(realbase())
    LDA     #$00
    BEQ     .Normal
    LDA     $5A    ;this gets the send amount
    STA     !energylink_weapon
    LDA     #$00
    BEQ     .Set
    .Set:
    JMP     $AEFD
    .Normal:
    LDX     $32
    BEQ     .BusterEquipped
    JMP     $AEE0
    .BusterEquipped:
    JMP     $AEFD

EnergylinkHealth:
    ; called if you pick up health Energy
    LDA     EnergylinkEnergy+1
    BEQ     .Normal
    LDA     $5A
    STA     !energylink_health
    JMP     $AEFD
    .Normal:
    LDX     #$00
    JMP     $AEE0

EnergylinkOneUp:
    LDA     EnergylinkEnergy+1
    BEQ     .Normal
    LDA     #$01
    STA     !energylink_lives
    JMP     $AEB9
    .Normal:
    LDA     $BF
    CMP     #$09
    JMP     $AED2




%org($FDE7, $1F)
EnableSaveRam:
    STA     $FE
    LDA     #$80
    STA     $A001
    LDA     #$00
    LDX     #$00
    .Loop:
    STA     $6000, X
    INX
    CPX     #$00
    BNE     .Loop
    .Return:
    LDA     #$01
    JMP     $FE64


%org($FE60, $1F)
    JMP     EnableSaveRam
    NOP