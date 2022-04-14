export class Naming {
  public static appName: string = "account-setup";
  public static env: string = process.env.ENV ? process.env.ENV : "dev";

  public static of(name: string): string {
    return `${this.appName}-${this.env}-${name}`;
  }
}