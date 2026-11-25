import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = in.nextInt();
        long[] h = new long[n];
        for (int i = 0; i < n; i++) {
            h[i] = in.nextLong();
        }
        long[] dp = new long[n];
        for (int i = 1; i < n; i++) {
            dp[i] = dp[i - 1] + Math.abs(h[i] - h[i - 1]);
            if (i > 1) {
                dp[i] = Math.min(dp[i], dp[i - 2] + Math.abs(h[i] - h[i - 2]));
            }
        }
        System.out.println(dp[n - 1]);
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
