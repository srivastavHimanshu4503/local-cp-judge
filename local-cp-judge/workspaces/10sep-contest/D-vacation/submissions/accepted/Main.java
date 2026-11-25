import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        if (!in.hasNext()) return;
        int n = in.nextInt();
        long a = 0, b = 0, c = 0;
        for (int i = 0; i < n; i++) {
            long x = in.nextLong();
            long y = in.nextLong();
            long z = in.nextLong();
            long na = x + Math.max(b, c);
            long nb = y + Math.max(a, c);
            long nc = z + Math.max(a, b);
            a = na;
            b = nb;
            c = nc;
        }
        System.out.println(Math.max(a, Math.max(b, c)));
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
