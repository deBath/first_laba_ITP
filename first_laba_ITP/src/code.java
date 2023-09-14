import java.util.Scanner;

// Press Shift twice to open the Search Everywhere dialog and type `show whitespaces`,
// then press Enter. You can now see whitespace characters in your code.
public class code {
    public static void main(String[] args) {
        Scanner scan = new Scanner(System.in);
        System.out.print("Введите своё имя: ");
        String name = scan.nextLine();
        System.out.print("Приветствуем, " + name + "!");
        System.out.println("Удачного дня и веселого настроения!");
    }
}