package com.example.Minelink;

import org.bukkit.Bukkit;
import org.bukkit.Server;
import org.bukkit.plugin.java.JavaPlugin;
import org.java_websocket.WebSocket;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.server.WebSocketServer;
import org.json.JSONObject;

import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.List;

public class Minelink extends JavaPlugin {
    private WebSocketServerImpl wsServer;
    private static final int PORT = 23089;

    @Override
    public void onEnable() {
        wsServer = new WebSocketServerImpl(PORT);
        wsServer.start();

        getLogger().info("Minelink插件已启动，WebSocket服务器运行在端口: " + PORT);
    }

    @Override
    public void onDisable() {
        if (wsServer != null) {
            try {
                wsServer.stop();
            } catch (Exception e) {
                getLogger().warning("关闭WebSocket服务器时发生错误: " + e.getMessage());
            }
        }
        getLogger().info("Minelink插件已禁用");
    }

    private class WebSocketServerImpl extends WebSocketServer {
        public WebSocketServerImpl(int port) {
            super(new InetSocketAddress(port));
        }

        @Override
        public void onOpen(WebSocket conn, ClientHandshake handshake) {
            getLogger().info("新的WebSocket连接: " + conn.getRemoteSocketAddress());
        }

        @Override
        public void onClose(WebSocket conn, int code, String reason, boolean remote) {
            getLogger().info("WebSocket连接关闭: " + conn.getRemoteSocketAddress());
        }

        @Override
        public void onMessage(WebSocket conn, String message) {
            JSONObject response = new JSONObject();

            try {
                switch (message.toLowerCase()) {
                    case "load" -> {
                        Runtime runtime = Runtime.getRuntime();
                        long maxMemory = runtime.maxMemory() / 1024 / 1024;
                        long allocatedMemory = runtime.totalMemory() / 1024 / 1024;
                        long freeMemory = runtime.freeMemory() / 1024 / 1024;
                        double[] tps = Bukkit.getServer().getTPS();
                        response.put("response", String.format(
                                "服务器状态:\n" +
                                "最大内存: %dMB\n" +
                                "已分配内存: %dMB\n" +
                                "空闲内存: %dMB\n" +
                                "TPS: %.2f\n" + // 使用 %.2f 格式化 double 类型的值
                                "在线玩家: %d/%d",
                                maxMemory,
                                allocatedMemory,
                                freeMemory,
                                tps[0], 
                                Bukkit.getOnlinePlayers().size(),
                                Bukkit.getMaxPlayers()));
                    }
                    case "log" -> {
                        response.put("response", "最近的服务器日志:TODO 呃呃理论上读文件就可以了但是我懒");
                    }
                    default -> {
                        Bukkit.getScheduler().runTask(Minelink.this, () -> {
                            boolean success = Bukkit.dispatchCommand(Bukkit.getConsoleSender(), message);
                            JSONObject cmdResponse = new JSONObject();
                            cmdResponse.put("response", success ? "命令执行成功" : "命令执行失败");
                            conn.send(cmdResponse.toString());
                        });
                        return;
                    }
                }
            } catch (Exception e) {
                response.put("response", "执行命令时发生错误: " + e.getMessage());
            }

            conn.send(response.toString());
        }

        @Override
        public void onError(WebSocket conn, Exception ex) {
            getLogger().warning("WebSocket错误: " + ex.getMessage());
        }

        @Override
        public void onStart() {
            getLogger().info("WebSocket服务器已启动");
        }
    }
}