package com.example.sheetmusic;

import net.minecraft.block.BlockState;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

/** 서버에서 매 틱 악보를 한 칸씩 진행하며 소리를 낸다. */
public class PianoBlockEntity extends BlockEntity {
    private int[] steps = new int[0];
    private int tempo = 5;
    private int index;
    private int end;
    private int wait;
    private boolean playing;

    public PianoBlockEntity(BlockPos pos, BlockState state) {
        super(SheetMusicMod.PIANO_BE, pos, state);
    }

    public void start(int[] steps, int tempo) {
        this.steps = steps.clone();
        this.tempo = Math.max(1, tempo);
        this.end = 0;
        for (int i = 0; i < steps.length; i++) {
            if (steps[i] != 0) end = i + 1;
        }
        this.index = 0;
        this.wait = 0;
        this.playing = end > 0;
    }

    public void stop() {
        playing = false;
    }

    public boolean isPlaying() {
        return playing;
    }

    public static void tick(World world, BlockPos pos, BlockState state, PianoBlockEntity be) {
        if (!be.playing) return;
        if (be.wait > 0) {
            be.wait--;
            return;
        }
        if (be.index >= be.end) {
            be.playing = false;
            return;
        }
        int mask = be.steps[be.index++];
        for (int n = 0; n <= SheetMusicMod.MAX_NOTE; n++) {
            if ((mask & (1 << n)) == 0) continue;
            world.playSound(null, pos, SheetMusicMod.harp(), SoundCategory.RECORDS, 3.0f, SheetMusicMod.pitchOf(n));
            if (world instanceof ServerWorld sw) {
                sw.spawnParticles(ParticleTypes.NOTE, pos.getX() + 0.5, pos.getY() + 1.2, pos.getZ() + 0.5,
                        0, n / 24.0, 0.0, 0.0, 1.0);
            }
        }
        be.wait = be.tempo - 1;
    }
}
