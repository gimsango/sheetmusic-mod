package com.example.sheetmusic;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.networking.v1.PacketByteBufs;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.client.gui.widget.TextFieldWidget;
import net.minecraft.client.sound.PositionedSoundInstance;
import net.minecraft.item.ItemStack;
import net.minecraft.network.PacketByteBuf;
import net.minecraft.text.Text;
import net.minecraft.util.Hand;
import net.minecraft.util.Identifier;

/** 펼친 책 모양의 악보 편집 화면. 오른쪽 페이지가 피아노 롤(16칸 x 25음), 왼쪽 페이지가 메뉴. */
public class SheetMusicScreen extends Screen {
    private static final Identifier BOOK = new Identifier(SheetMusicMod.MOD_ID, "textures/gui/sheet_music_book.png");
    private static final int W = 256, H = 180;
    private static final int CELL = 6, COLS = 16, ROWS = SheetMusicMod.MAX_NOTE + 1;
    private static final int GX = 144, GY = 14;
    private static final int PAGES = SheetMusicMod.MAX_STEPS / COLS;
    private static final int INK = 0xFF3B2A14;
    private static final String[] NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

    private final Hand hand;
    private final int[] steps = new int[SheetMusicMod.MAX_STEPS];
    private final String initialTitle;
    private int tempo;
    private int page;
    private boolean dirty;

    private TextFieldWidget titleField;
    private ButtonWidget playButton;
    private int left, top;

    // 미리듣기 상태
    private boolean previewing;
    private int previewIndex, previewWait, previewEnd, playingStep = -1;

    public SheetMusicScreen(ItemStack stack, Hand hand) {
        super(Text.translatable("gui.sheetmusic.title"));
        this.hand = hand;
        int[] saved = SheetMusicItem.getSteps(stack);
        System.arraycopy(saved, 0, steps, 0, Math.min(saved.length, steps.length));
        this.tempo = SheetMusicItem.getTempo(stack);
        this.initialTitle = SheetMusicItem.getTitle(stack);
    }

    static String noteName(int n) {
        int midi = 54 + n; // n=0 -> F#3
        return NAMES[midi % 12] + (midi / 12 - 1);
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = (height - H) / 2;

        String title = titleField != null ? titleField.getText() : initialTitle;
        titleField = new TextFieldWidget(textRenderer, left + 14, top + 21, 102, 14, Text.translatable("gui.sheetmusic.title"));
        titleField.setMaxLength(32);
        titleField.setText(title);
        titleField.setChangedListener(s -> dirty = true);
        addDrawableChild(titleField);

        addDrawableChild(ButtonWidget.builder(Text.literal("-"), b -> changeTempo(1)).dimensions(left + 14, top + 42, 24, 16).build());
        addDrawableChild(ButtonWidget.builder(Text.literal("+"), b -> changeTempo(-1)).dimensions(left + 92, top + 42, 24, 16).build());
        addDrawableChild(ButtonWidget.builder(Text.literal("<"), b -> changePage(-1)).dimensions(left + 14, top + 64, 24, 16).build());
        addDrawableChild(ButtonWidget.builder(Text.literal(">"), b -> changePage(1)).dimensions(left + 92, top + 64, 24, 16).build());

        playButton = ButtonWidget.builder(Text.translatable(previewing ? "gui.sheetmusic.stop" : "gui.sheetmusic.play"),
                b -> togglePreview()).dimensions(left + 14, top + 88, 102, 16).build();
        addDrawableChild(playButton);
        addDrawableChild(ButtonWidget.builder(Text.translatable("gui.sheetmusic.clear_page"), b -> clearPage())
                .dimensions(left + 14, top + 108, 102, 16).build());
        addDrawableChild(ButtonWidget.builder(Text.translatable("gui.sheetmusic.done"), b -> close())
                .dimensions(left + 14, top + 128, 102, 16).build());
    }

    private void changeTempo(int d) {
        tempo = Math.max(2, Math.min(20, tempo + d));
        dirty = true;
    }

    private void changePage(int d) {
        page = Math.max(0, Math.min(PAGES - 1, page + d));
    }

    private void clearPage() {
        for (int i = 0; i < COLS; i++) steps[page * COLS + i] = 0;
        dirty = true;
    }

    private void togglePreview() {
        if (previewing) {
            stopPreview();
            return;
        }
        previewEnd = 0;
        for (int i = 0; i < steps.length; i++) {
            if (steps[i] != 0) previewEnd = i + 1;
        }
        if (previewEnd == 0) return;
        previewing = true;
        previewIndex = page * COLS;
        previewWait = 0;
        playingStep = -1;
        playButton.setMessage(Text.translatable("gui.sheetmusic.stop"));
    }

    private void stopPreview() {
        previewing = false;
        playingStep = -1;
        if (playButton != null) playButton.setMessage(Text.translatable("gui.sheetmusic.play"));
    }

    private void playNote(int n) {
        client.getSoundManager().play(PositionedSoundInstance.master(SheetMusicMod.harp(), SheetMusicMod.pitchOf(n), 1.0f));
    }

    @Override
    public void tick() {
        if (!previewing) return;
        if (previewWait > 0) {
            previewWait--;
            return;
        }
        if (previewIndex >= previewEnd) {
            stopPreview();
            return;
        }
        playingStep = previewIndex;
        page = playingStep / COLS;
        int mask = steps[previewIndex++];
        for (int n = 0; n < ROWS; n++) {
            if ((mask & (1 << n)) != 0) playNote(n);
        }
        previewWait = tempo - 1;
    }

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        if (super.mouseClicked(mx, my, button)) return true;
        double rx = mx - (left + GX), ry = my - (top + GY);
        if (rx >= 0 && ry >= 0 && rx < COLS * CELL && ry < ROWS * CELL) {
            int idx = page * COLS + (int) (rx / CELL);
            int n = ROWS - 1 - (int) (ry / CELL);
            if (button == 0) {
                steps[idx] ^= (1 << n);
                if ((steps[idx] & (1 << n)) != 0) playNote(n);
            } else if (button == 1) {
                steps[idx] = 0;
            }
            dirty = true;
            return true;
        }
        return false;
    }

    @Override
    public void render(DrawContext ctx, int mx, int my, float delta) {
        renderBackground(ctx);
        ctx.drawTexture(BOOK, left, top, 0, 0, W, H);

        drawLabel(ctx, Text.translatable("gui.sheetmusic.title"), left + 14, top + 11);
        drawCentered(ctx, Text.translatable("gui.sheetmusic.bpm", 600 / tempo), left + 65, top + 46);
        drawCentered(ctx, Text.translatable("gui.sheetmusic.page", page + 1, PAGES), left + 65, top + 68);

        drawGrid(ctx, mx, my);
        super.render(ctx, mx, my, delta);
    }

    private void drawLabel(DrawContext ctx, Text text, int x, int y) {
        ctx.drawText(textRenderer, text, x, y, INK, false);
    }

    private void drawCentered(DrawContext ctx, Text text, int cx, int y) {
        ctx.drawText(textRenderer, text, cx - textRenderer.getWidth(text) / 2, y, INK, false);
    }

    private void drawGrid(DrawContext ctx, int mx, int my) {
        int gx = left + GX, gy = top + GY;
        int gw = COLS * CELL, gh = ROWS * CELL;

        // 건반 색(검은 건반 행은 어둡게) + 도(C) 경계선 + 작은 라벨
        for (int r = 0; r < ROWS; r++) {
            int n = ROWS - 1 - r;
            int pc = (54 + n) % 12;
            int y = gy + r * CELL;
            if (pc == 1 || pc == 3 || pc == 6 || pc == 8 || pc == 10) {
                ctx.fill(gx, y, gx + gw, y + CELL, 0x30000000);
            }
            if (pc == 0) {
                ctx.fill(gx, y + CELL - 1, gx + gw, y + CELL, 0x80805020);
                var m = ctx.getMatrices();
                m.push();
                m.scale(0.5f, 0.5f, 1f);
                ctx.drawText(textRenderer, noteName(n), (gx - 11) * 2, (y + 1) * 2, INK, false);
                m.pop();
            }
        }
        // 박자선
        for (int c = 0; c <= COLS; c++) {
            ctx.fill(gx + c * CELL, gy, gx + c * CELL + 1, gy + gh, c % 4 == 0 ? 0x60000000 : 0x20000000);
        }
        ctx.fill(gx, gy + gh, gx + gw + 1, gy + gh + 1, 0x60000000);

        // 재생 중인 열 강조
        if (previewing && playingStep >= page * COLS && playingStep < (page + 1) * COLS) {
            int x = gx + (playingStep - page * COLS) * CELL;
            ctx.fill(x, gy, x + CELL, gy + gh, 0x5538A838);
        }

        // 음표
        for (int c = 0; c < COLS; c++) {
            int mask = steps[page * COLS + c];
            if (mask == 0) continue;
            for (int n = 0; n < ROWS; n++) {
                if ((mask & (1 << n)) == 0) continue;
                int x = gx + c * CELL, y = gy + (ROWS - 1 - n) * CELL;
                ctx.fill(x + 1, y + 1, x + CELL, y + CELL, 0xFFB5381E);
            }
        }

        // 마우스 오버
        double rx = mx - gx, ry = my - gy;
        if (rx >= 0 && ry >= 0 && rx < gw && ry < gh) {
            int c = (int) (rx / CELL), r = (int) (ry / CELL);
            ctx.fill(gx + c * CELL, gy + r * CELL, gx + c * CELL + CELL, gy + r * CELL + CELL, 0x5540A0FF);
            drawLabel(ctx, Text.translatable("gui.sheetmusic.note", noteName(ROWS - 1 - r)), left + 14, top + 150);
        }
        drawLabel(ctx, Text.translatable("gui.sheetmusic.hint"), left + 14, top + 161);
    }

    private void save() {
        if (!dirty) return;
        int last = 0;
        for (int i = 0; i < steps.length; i++) {
            if (steps[i] != 0) last = i + 1;
        }
        int len = last == 0 ? 0 : ((last + COLS - 1) / COLS) * COLS;
        int[] out = new int[len];
        System.arraycopy(steps, 0, out, 0, len);

        PacketByteBuf buf = PacketByteBufs.create();
        buf.writeEnumConstant(hand);
        buf.writeString(titleField.getText());
        buf.writeVarInt(tempo);
        buf.writeIntArray(out);
        ClientPlayNetworking.send(SheetMusicMod.SAVE_PACKET, buf);
        dirty = false;
    }

    @Override
    public void removed() {
        save();
    }

    @Override
    public boolean shouldPause() {
        return false;
    }
}
