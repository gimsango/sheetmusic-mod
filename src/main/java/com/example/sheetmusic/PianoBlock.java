package com.example.sheetmusic;

import net.minecraft.block.Block;
import net.minecraft.block.BlockRenderType;
import net.minecraft.block.BlockState;
import net.minecraft.block.BlockWithEntity;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.block.entity.BlockEntityTicker;
import net.minecraft.block.entity.BlockEntityType;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.item.ItemStack;
import net.minecraft.state.StateManager;
import net.minecraft.state.property.DirectionProperty;
import net.minecraft.state.property.Properties;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.BlockMirror;
import net.minecraft.util.BlockRotation;
import net.minecraft.util.Hand;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.world.World;
import org.jetbrains.annotations.Nullable;

public class PianoBlock extends BlockWithEntity {
    public static final DirectionProperty FACING = Properties.HORIZONTAL_FACING;

    public PianoBlock(Settings settings) {
        super(settings);
        setDefaultState(getStateManager().getDefaultState().with(FACING, Direction.NORTH));
    }

    @Override
    protected void appendProperties(StateManager.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getPlacementState(ItemPlacementContext ctx) {
        return getDefaultState().with(FACING, ctx.getHorizontalPlayerFacing().getOpposite());
    }

    @Override
    public BlockState rotate(BlockState state, BlockRotation rotation) {
        return state.with(FACING, rotation.rotate(state.get(FACING)));
    }

    @Override
    public BlockState mirror(BlockState state, BlockMirror mirror) {
        return state.rotate(mirror.getRotation(state.get(FACING)));
    }

    // BlockWithEntity 기본값은 INVISIBLE 이라 반드시 MODEL 로 바꿔야 보임
    @Override
    public BlockRenderType getRenderType(BlockState state) {
        return BlockRenderType.MODEL;
    }

    @Nullable
    @Override
    public BlockEntity createBlockEntity(BlockPos pos, BlockState state) {
        return new PianoBlockEntity(pos, state);
    }

    @Nullable
    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(World world, BlockState state, BlockEntityType<T> type) {
        return world.isClient ? null : checkType(type, SheetMusicMod.PIANO_BE, PianoBlockEntity::tick);
    }

    @Override
    public ActionResult onUse(BlockState state, World world, BlockPos pos, PlayerEntity player, Hand hand, BlockHitResult hit) {
        BlockEntity be = world.getBlockEntity(pos);
        if (!(be instanceof PianoBlockEntity piano)) {
            return ActionResult.PASS;
        }
        ItemStack stack = player.getStackInHand(hand);

        // 악보를 들고 우클릭 -> 연주 시작
        if (stack.getItem() instanceof SheetMusicItem) {
            if (!world.isClient) {
                int[] steps = SheetMusicItem.getSteps(stack);
                if (!SheetMusicItem.hasNotes(steps)) {
                    player.sendMessage(Text.translatable("message.sheetmusic.empty"), true);
                } else {
                    piano.start(steps, SheetMusicItem.getTempo(stack));
                    player.sendMessage(Text.translatable("message.sheetmusic.playing"), true);
                }
            }
            return ActionResult.success(world.isClient);
        }

        // 빈 손 우클릭 -> 연주 정지 / 안내
        if (stack.isEmpty() && hand == Hand.MAIN_HAND && !(player.getOffHandStack().getItem() instanceof SheetMusicItem)) {
            if (!world.isClient) {
                if (piano.isPlaying()) {
                    piano.stop();
                    player.sendMessage(Text.translatable("message.sheetmusic.stopped"), true);
                } else {
                    player.sendMessage(Text.translatable("message.sheetmusic.hint"), true);
                }
            }
            return ActionResult.success(world.isClient);
        }
        return ActionResult.PASS;
    }
}
