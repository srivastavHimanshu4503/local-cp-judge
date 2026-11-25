import java.io.*;
import java.util.*;

class Main {
    // ---------------- your code starts here ----------------
    // s: encoded string of digits
    // return total number of valid decodings (1..26 -> A..Z)
    static long solve(String s) {
        return 0L;
    }
    // ----------------- your code ends here -----------------

    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) continue;
            if (line.equals("0")) break;
            sb.append(solve(line)).append('\n');
        }
        System.out.print(sb);
    }
}
