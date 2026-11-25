import java.io.*;
import java.util.*;

class Main {
    // ---------------- your code starts here ----------------
    // h[0..n-1]: heights of the N stones
    // return the minimum total cost to reach stone n - 1
    static int solve(int n, int[] h) {
        return 0;
    }
    // ----------------- your code ends here -----------------

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = in.nextInt();
        int[] h = new int[n];
        for (int i = 0; i < n; i++) {
            h[i] = in.nextInt();
        }
        System.out.println(solve(n, h));
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
