/**
 * Java Competitive Programming Starter Template
 * Local CP Judge
 */

import java.io.BufferedReader;
import java.io.BufferedOutputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.io.IOException;
import java.util.StringTokenizer;

public class Main {
    static class FastScanner {
        private final BufferedReader reader;
        private StringTokenizer tokenizer;

        public FastScanner() {
            reader = new BufferedReader(new InputStreamReader(System.in));
            tokenizer = new StringTokenizer("");
        }

        public String next() {
            while (!tokenizer.hasMoreTokens()) {
                String line = null;
                try {
                    line = reader.readLine();
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
                if (line == null) {
                    return null;
                }
                tokenizer = new StringTokenizer(line);
            }
            return tokenizer.nextToken();
        }

        public int nextInt() {
            String token = next();
            if (token == null) {
                throw new RuntimeException("Unexpected end of input");
            }
            return Integer.parseInt(token);
        }

        public long nextLong() {
            String token = next();
            if (token == null) {
                throw new RuntimeException("Unexpected end of input");
            }
            return Long.parseLong(token);
        }

        public double nextDouble() {
            String token = next();
            if (token == null) {
                throw new RuntimeException("Unexpected end of input");
            }
            return Double.parseDouble(token);
        }

        public String nextLine() {
            try {
                return reader.readLine();
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
    }

    public static void solve(FastScanner in, PrintWriter out) {
        // Read input and implement problem logic here
    }

    public static void main(String[] args) {
        FastScanner in = new FastScanner();
        PrintWriter out = new PrintWriter(new BufferedOutputStream(System.out));

        int testCases = 1;
        // testCases = in.nextInt(); // Uncomment if problem contains multiple test cases
        for (int t = 0; t < testCases; t++) {
            solve(in, out);
        }

        out.flush();
    }
}
