import java.io.*;
import java.util.*;

class Main {
    // ---------------- your code starts here ----------------
    // grid is an h x w chamber grid of stone counts
    // return the maximum stones collected reaching the bottom row
    static int solve(int h, int w, int[][] grid) {
        return 0;
    }
    // ----------------- your code ends here -----------------

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int t = in.nextInt();
        StringBuilder sb = new StringBuilder();
        for (int tc = 0; tc < t; tc++) {
            int h = in.nextInt();
            int w = in.nextInt();
            int[][] grid = new int[h][w];
            for (int i = 0; i < h; i++) {
                for (int j = 0; j < w; j++) {
                    grid[i][j] = in.nextInt();
                }
            }
            sb.append(solve(h, w, grid)).append('\n');
        }
        System.out.print(sb);
    }

    static class FastReader {
        private final DataInputStream in;
        private final byte[] buf = new byte[1 << 16];
        private int len = 0, ptr = 0;

        FastReader(InputStream is) { in = new DataInputStream(is); }

        private int read() throws IOException {
            if (ptr == len) { len = in.read(buf, 0, buf.length); ptr = 0; if (len <= 0) return -1; }
            return buf[ptr++];
        }

        int nextInt() throws IOException {
            int c = read();
            while (c != -1 && c <= ' ') c = read();
            boolean neg = false;
            if (c == '-') { neg = true; c = read(); }
            int r = 0;
            while (c >= '0' && c <= '9') { r = r * 10 + (c - '0'); c = read(); }
            return neg ? -r : r;
        }
    }
}
