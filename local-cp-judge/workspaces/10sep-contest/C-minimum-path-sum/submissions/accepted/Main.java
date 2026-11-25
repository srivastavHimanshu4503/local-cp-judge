import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        if (!in.hasNext()) return;
        int m = in.nextInt();
        int n = in.nextInt();
        long[][] grid = new long[m][n];
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                grid[i][j] = in.nextLong();
            }
        }
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                if (i == 0 && j == 0) continue;
                long best = Long.MAX_VALUE;
                if (i > 0) best = Math.min(best, grid[i - 1][j]);
                if (j > 0) best = Math.min(best, grid[i][j - 1]);
                grid[i][j] += best;
            }
        }
        System.out.println(grid[m - 1][n - 1]);
    }

    static class FastReader {
        private final InputStream in;
        private final byte[] buf = new byte[1 << 16];
        private int len = 0, ptr = 0;

        FastReader(InputStream in) { this.in = in; }

        private int read() throws IOException {
            if (ptr == len) {
                len = in.read(buf, 0, buf.length);
                ptr = 0;
                if (len <= 0) return -1;
            }
            return buf[ptr++];
        }

        boolean hasNext() throws IOException {
            int c;
            while ((c = read()) != -1) {
                if (c > ' ') {
                    ptr--;
                    return true;
                }
            }
            return false;
        }

        int nextInt() throws IOException { return (int) nextLong(); }

        long nextLong() throws IOException {
            int c = read();
            while (c != -1 && c <= ' ') c = read();
            boolean neg = false;
            if (c == '-') { neg = true; c = read(); }
            long r = 0;
            while (c >= '0' && c <= '9') {
                r = r * 10 + (c - '0');
                c = read();
            }
            return neg ? -r : r;
        }
    }
}
