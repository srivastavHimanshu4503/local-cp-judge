import java.io.*;
import java.util.*;

public class Main {
    private static int minInsertions(String s) {
        int n = s.length();
        int[] prev = new int[n + 1];
        int[] curr = new int[n + 1];
        for (int i = 1; i <= n; i++) {
            char ci = s.charAt(i - 1);
            for (int j = 1; j <= n; j++) {
                char cj = s.charAt(n - j);
                if (ci == cj) {
                    curr[j] = prev[j - 1] + 1;
                } else {
                    curr[j] = Math.max(prev[j], curr[j - 1]);
                }
            }
            int[] tmp = prev;
            prev = curr;
            curr = tmp;
        }
        return n - prev[n];
    }

    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        List<String> tokens = new ArrayList<>();
        String line;
        while ((line = br.readLine()) != null) {
            StringTokenizer st = new StringTokenizer(line);
            while (st.hasMoreTokens()) {
                tokens.add(st.nextToken());
            }
        }
        if (tokens.isEmpty()) return;
        int t = Integer.parseInt(tokens.get(0));
        StringBuilder sb = new StringBuilder();
        for (int idx = 1; idx <= t && idx < tokens.size(); idx++) {
            sb.append(minInsertions(tokens.get(idx))).append('\n');
        }
        System.out.print(sb);
    }
}
