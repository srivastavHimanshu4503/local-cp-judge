import java.io.*;
import java.util.*;

class Main {
    // ---------------- your code starts here ----------------
    // return true if s is a subsequence of t, else false
    static boolean solve(String s, String t) {
        return false;
    }
    // ----------------- your code ends here -----------------

    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String s = br.readLine();
        String t = br.readLine();
        if (s == null) s = ""; else s = s.trim();
        if (t == null) t = ""; else t = t.trim();
        System.out.println(solve(s, t) ? "true" : "false");
    }
}
