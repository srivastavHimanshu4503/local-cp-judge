import java.io.*;
import java.util.*;

class Main {
    // ---------------- your code starts here ----------------
    // s: input lowercase string
    // return minimum number of character insertions to make s a palindrome
    static int solve(String s) {
        return 0;
    }
    // ----------------- your code ends here -----------------

    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String first = br.readLine();
        while (first != null && first.trim().isEmpty()) first = br.readLine();
        if (first == null) return;
        int t = Integer.parseInt(first.trim());
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < t; i++) {
            String s = br.readLine();
            while (s != null && s.trim().isEmpty()) s = br.readLine();
            if (s == null) break;
            sb.append(solve(s.trim())).append('\n');
        }
        System.out.print(sb);
    }
}
