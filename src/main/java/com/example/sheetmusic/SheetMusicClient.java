package com.example.sheetmusic;

import net.fabricmc.api.ClientModInitializer;
import net.minecraft.client.MinecraftClient;

public class SheetMusicClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        SheetMusicItem.screenOpener = (stack, hand) ->
                MinecraftClient.getInstance().setScreen(new SheetMusicScreen(stack, hand));
    }
}
