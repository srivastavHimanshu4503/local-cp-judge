import java.io.*;
import java.util.*;

class Main {
    // ---------------- your code starts here ----------------
    // grid is an m x n matrix of non-negative integers
    // return the minimum path sum from (0, 0) to (m - 1, n - 1)
    static int solve(int m, int n, int[][] grid) {
        return 0;
    }
    // ----------------- your code ends here -----------------

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int m = in.nextInt();
        int n = in.nextInt();
        int[][] grid = new int[m][n];
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                grid[i][j] = in.nextInt();
            }
        }
        System.out.println(solve(m, n, grid));
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
