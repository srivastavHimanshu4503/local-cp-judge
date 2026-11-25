import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        if (!in.hasNext()) return;
        int t = in.nextInt();
        StringBuilder sb = new StringBuilder();
        while (t-- > 0) {
            int h = in.nextInt();
            int w = in.nextInt();
            long[] dp = new long[w];
            for (int j = 0; j < w; j++) {
                dp[j] = in.nextLong();
            }
            for (int r = 1; r < h; r++) {
                long[] next = new long[w];
                for (int j = 0; j < w; j++) {
                    long val = in.nextLong();
                    long best = dp[j];
                    if (j > 0) best = Math.max(best, dp[j - 1]);
                    if (j + 1 < w) best = Math.max(best, dp[j + 1]);
                    next[j] = val + best;
                }
                dp = next;
            }
            long ans = 0;
            for (long v : dp) ans = Math.max(ans, v);
            sb.append(ans).append('\n');
        }
        System.out.print(sb);
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
