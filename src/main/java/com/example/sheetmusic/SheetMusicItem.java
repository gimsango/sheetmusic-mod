package com.example.sheetmusic;

import net.minecraft.client.item.TooltipContext;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.nbt.NbtElement;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.world.World;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * 악보 아이템.
 * NBT: Steps(int[]; 칸마다 25비트 마스크 = 동시에 울릴 음), Tempo(int; 한 칸당 틱 수), Title(String)
 */
public class SheetMusicItem extends Item {
    public interface ScreenOpener {
        void open(ItemStack stack, Hand hand);
    }

    /** 클라이언트 초기화에서 교체됨 (서버에서 클라이언트 클래스를 건드리지 않기 위함) */
    public static ScreenOpener screenOpener = (stack, hand) -> {};

    public SheetMusicItem(Settings settings) {
        super(settings);
    }

    @Override
    public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
        ItemStack stack = user.getStackInHand(hand);
        if (world.isClient) {
            screenOpener.open(stack, hand);
        }
        return TypedActionResult.success(stack, world.isClient);
    }

    @Override
    public void appendTooltip(ItemStack stack, @Nullable World world, List<Text> tooltip, TooltipContext context) {
        String title = getTitle(stack);
        if (!title.isEmpty()) {
            tooltip.add(Text.literal(title).formatted(Formatting.GRAY));
        }
        int count = 0;
        for (int mask : getSteps(stack)) {
            count += Integer.bitCount(mask);
        }
        tooltip.add(Text.translatable("tooltip.sheetmusic.info", count, 600 / getTempo(stack))
                .formatted(Formatting.DARK_GRAY));
    }

    public static int[] getSteps(ItemStack stack) {
        NbtCompound nbt = stack.getNbt();
        if (nbt != null && nbt.contains("Steps", NbtElement.INT_ARRAY_TYPE)) {
            return nbt.getIntArray("Steps");
        }
        return new int[0];
    }

    public static int getTempo(ItemStack stack) {
        NbtCompound nbt = stack.getNbt();
        int t = (nbt != null && nbt.contains("Tempo")) ? nbt.getInt("Tempo") : 5;
        return Math.max(2, Math.min(20, t));
    }

    public static String getTitle(ItemStack stack) {
        NbtCompound nbt = stack.getNbt();
        return nbt != null ? nbt.getString("Title") : "";
    }

    public static boolean hasNotes(int[] steps) {
        for (int s : steps) {
            if (s != 0) return true;
        }
        return false;
    }

    public static void write(ItemStack stack, String title, int tempo, int[] steps) {
        NbtCompound nbt = stack.getOrCreateNbt();
        int[] clean = new int[Math.min(steps.length, SheetMusicMod.MAX_STEPS)];
        int mask25 = (1 << (SheetMusicMod.MAX_NOTE + 1)) - 1;
        for (int i = 0; i < clean.length; i++) {
            clean[i] = steps[i] & mask25;
        }
        if (hasNotes(clean)) {
            nbt.putIntArray("Steps", clean);
        } else {
            nbt.remove("Steps");
        }
        nbt.putInt("Tempo", Math.max(2, Math.min(20, tempo)));
        String t = title == null ? "" : title.trim();
        if (t.isEmpty()) {
            nbt.remove("Title");
        } else {
            nbt.putString("Title", t);
        }
    }
}
