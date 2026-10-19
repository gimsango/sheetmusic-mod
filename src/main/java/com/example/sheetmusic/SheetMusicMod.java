package com.example.sheetmusic;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Blocks;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.sound.SoundEvent;
import net.minecraft.text.Text;
import net.minecraft.util.Hand;
import net.minecraft.util.Identifier;

public class SheetMusicMod implements ModInitializer {
    public static final String MOD_ID = "sheetmusic";
    public static final Identifier SAVE_PACKET = new Identifier(MOD_ID, "save_sheet");

    /** 악보 한 장의 최대 길이 (16칸 x 8페이지) */
    public static final int MAX_STEPS = 128;
    /** 음 번호 0..24 (F#3 ~ F#5, 노트블록과 같은 2옥타브 범위) */
    public static final int MAX_NOTE = 24;

    public static final Item SHEET_MUSIC = new SheetMusicItem(new Item.Settings().maxCount(16));
    public static final PianoBlock PIANO = new PianoBlock(AbstractBlock.Settings.copy(Blocks.OAK_PLANKS).strength(2.0f));
    public static final Item PIANO_ITEM = new BlockItem(PIANO, new Item.Settings());
    public static BlockEntityType<PianoBlockEntity> PIANO_BE;

    private static SoundEvent harp;

    public static Identifier id(String path) {
        return new Identifier(MOD_ID, path);
    }

    /** 노트블록 '하프' 소리 (피아노 느낌으로 사용) */
    public static SoundEvent harp() {
        if (harp == null) {
            harp = Registries.SOUND_EVENT.get(new Identifier("block.note_block.harp"));
        }
        return harp;
    }

    public static float pitchOf(int note) {
        return (float) Math.pow(2.0, (note - 12) / 12.0);
    }

    @Override
    public void onInitialize() {
        Registry.register(Registries.BLOCK, id("piano"), PIANO);
        Registry.register(Registries.ITEM, id("piano"), PIANO_ITEM);
        Registry.register(Registries.ITEM, id("sheet_music"), SHEET_MUSIC);
        PIANO_BE = Registry.register(Registries.BLOCK_ENTITY_TYPE, id("piano"),
                FabricBlockEntityTypeBuilder.create(PianoBlockEntity::new, PIANO).build());

        ItemGroup group = FabricItemGroup.builder()
                .icon(() -> new ItemStack(SHEET_MUSIC))
                .displayName(Text.translatable("itemGroup.sheetmusic"))
                .entries((ctx, entries) -> {
                    entries.add(SHEET_MUSIC);
                    entries.add(PIANO_ITEM);
                })
                .build();
        Registry.register(Registries.ITEM_GROUP, id("main"), group);

        // 클라이언트 GUI에서 저장 -> 서버가 손에 든 악보에 기록
        ServerPlayNetworking.registerGlobalReceiver(SAVE_PACKET, (server, player, handler, buf, sender) -> {
            Hand hand = buf.readEnumConstant(Hand.class);
            String title = buf.readString(32);
            int tempo = buf.readVarInt();
            int[] steps = buf.readIntArray(MAX_STEPS);
            server.execute(() -> {
                ItemStack stack = player.getStackInHand(hand);
                if (stack.getItem() instanceof SheetMusicItem) {
                    SheetMusicItem.write(stack, title, tempo, steps);
                }
            });
        });
    }
}
